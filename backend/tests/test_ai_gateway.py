import json
import httpx
import pytest
from sqlalchemy import select
from app.config import settings
from app.models import Notification
from app.schemas import DocumentInput
from app.services.ai import available_models, complete_json
from app.services.documents import save_document, summarize_document

SOURCE = "O fundo informou receita de R$ 10 milhões no trimestre e manteve a distribuição mensal."
SUMMARY = {
    "facts": [{"fact": "O fundo informou receita trimestral.", "evidence": SOURCE}],
    "risks": [],
    "interpretations": [],
    "missing": ["Vacância não informada."],
}


@pytest.fixture
def lm_config(monkeypatch):
    config = settings()
    monkeypatch.setattr(config, "ai_provider", "lmstudio")
    monkeypatch.setattr(config, "lm_studio_base_url", "http://localhost:1235/v1/")
    monkeypatch.setattr(config, "lm_studio_model", "test-local-model")
    monkeypatch.setattr(config, "lm_studio_api_key", "gateway-secret-test")
    return config


def response(content=SUMMARY, finish_reason="stop"):
    return {"choices": [{"finish_reason": finish_reason, "message": {"content": json.dumps(content)}}]}


def test_lmstudio_chat_contract_auth_and_schema(lm_config):
    def transport(request):
        assert str(request.url) == "http://localhost:1235/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer gateway-secret-test"
        payload = json.loads(request.content)
        assert payload["model"] == "test-local-model"
        assert payload["response_format"]["type"] == "json_schema"
        assert payload["response_format"]["json_schema"]["strict"] is True
        assert payload["stream"] is False
        assert payload["temperature"] == 0
        return httpx.Response(200, json=response())

    client = httpx.Client(transport=httpx.MockTransport(transport))
    assert complete_json([{"role": "user", "content": SOURCE}], client)["facts"][0]["evidence"] == SOURCE


def test_lmstudio_optional_token_and_models(lm_config, monkeypatch):
    monkeypatch.setattr(lm_config, "lm_studio_api_key", "")

    def transport(request):
        assert "authorization" not in request.headers
        assert str(request.url) == "http://localhost:1235/v1/models"
        return httpx.Response(200, json={"data": [{"id": "test-local-model"}]})

    assert available_models(httpx.Client(transport=httpx.MockTransport(transport))) == ["test-local-model"]


@pytest.mark.parametrize(
    "payload",
    [
        response(finish_reason="length"),
        response({"facts": []}),
        {"choices": []},
        {"choices": [{"finish_reason": "stop", "message": {"content": "not json"}}]},
    ],
)
def test_lmstudio_rejects_truncated_or_invalid_output(lm_config, payload):
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)))
    with pytest.raises((ValueError, IndexError)):
        complete_json([], client)


def test_lmstudio_document_pipeline_preserves_evidence(db, lm_config):
    document = save_document(
        db,
        DocumentInput(
            ticker="HGLG11",
            title="Relatório de teste",
            source_url="https://example.com/report",
            text=SOURCE + " Informações adicionais do período.",
        ),
    )
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response())))
    summarize_document(db, document.id, client)
    assert document.status == "ready"
    assert document.summary["facts"][0]["evidence"] == SOURCE
    assert document.summary["sources"] == ["https://example.com/report"]
    assert db.scalar(select(Notification).where(Notification.event_key == f"summary:{document.id}"))
    summarize_document(db, document.id, client)
    assert len(db.scalars(select(Notification).where(Notification.category == "ai")).all()) == 1


def test_lmstudio_unavailable_is_visible_not_fallback(db, lm_config):
    document = save_document(
        db,
        DocumentInput(
            ticker="HGLG11", title="Relatório teste", source_url="https://example.com/report", text=SOURCE * 2
        ),
    )
    calls = []

    def transport(request):
        calls.append(str(request.url))
        raise httpx.ConnectError("unavailable", request=request)

    summarize_document(db, document.id, httpx.Client(transport=httpx.MockTransport(transport)))
    assert document.status == "failed"
    assert document.summary is None
    assert calls == ["http://localhost:1235/v1/chat/completions"]


def test_gateway_check_does_not_expose_token_or_send_documents(client, lm_config, monkeypatch):
    monkeypatch.setattr("app.main.available_models", lambda: ["test-local-model"])
    result = client.post("/api/ai/check")
    assert result.status_code == 200
    assert result.json()["model_available"] is True
    assert "gateway-secret-test" not in result.text
    integrations = client.get("/api/integrations").json()
    assert integrations["ai_provider"] == "lmstudio"
    assert integrations["ai_model"] == "test-local-model"
    assert "gateway-secret-test" not in json.dumps(integrations)


def test_ollama_is_explicit_alternative(lm_config, monkeypatch):
    monkeypatch.setattr(lm_config, "ai_provider", "ollama")
    monkeypatch.setattr(lm_config, "ollama_model", "alternative-local-model")

    def transport(request):
        assert str(request.url) == "http://localhost:11434/api/chat"
        assert "authorization" not in request.headers
        assert json.loads(request.content)["model"] == "alternative-local-model"
        return httpx.Response(
            200, json={"message": {"content": json.dumps(SUMMARY)}, "done": True, "done_reason": "stop"}
        )

    assert complete_json([], httpx.Client(transport=httpx.MockTransport(transport)))["facts"]


@pytest.mark.parametrize(
    "status,message,expected",
    [
        (400, "Failed to load model qwen: private/path", "não conseguiu carregar"),
        (401, "token gateway-secret-test invalid", "recusou a autenticação"),
    ],
)
def test_gateway_errors_are_actionable_and_redacted(db, lm_config, status, message, expected):
    document = save_document(
        db,
        DocumentInput(
            ticker="HGLG11", title="Relatório teste", source_url="https://example.com/report", text=SOURCE * 2
        ),
    )
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(status, json={"error": {"message": message}}))
    )
    summarize_document(db, document.id, client)
    assert document.status == "failed"
    assert expected in document.error
    assert "gateway-secret-test" not in document.error
    assert "private/path" not in document.error

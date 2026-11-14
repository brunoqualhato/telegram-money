"""Regressões da revisão, somente com dados fictícios e rede simulada."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import timedelta
import threading

import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base, utcnow
from app.models import Asset, Notification, ProcessingJob, Quote, ResourceLease
from app.services import ai, queue
from app.services.documents import save_document
from app.services.resources import resource_slot
from app.services.settings import get_app_setting, save_settings, validate_ai_url
from app.schemas import DocumentInput
from b3_fixtures import custody_xlsx

SOURCE = "A empresa fictícia informou receita de R$ 10 milhões no trimestre, sem alterações na distribuição."


def pending_document(db):
    return save_document(db, DocumentInput(
        ticker="TEST3", title="Relatório fictício de teste", source_url="https://example.com/report",
        text=SOURCE * 2,
    ))


@pytest.mark.parametrize("endpoint,payload", [
    ("test-ai", {"provider": "lmstudio", "url": "http://localhost:1235/v1"}),
    ("test-telegram", {"token": "123456:fake-test-token"}),
])
def test_public_integration_tests_close_after_setup(client, monkeypatch, endpoint, payload):
    def forbidden(*args, **kwargs):
        pytest.fail("Um teste público configurado não pode consultar a rede")
    monkeypatch.setattr("app.routers.system.test_ai_endpoint_live", forbidden)
    monkeypatch.setattr("app.routers.system.test_telegram_token_live", forbidden)
    client.cookies.clear()
    assert client.post(f"/api/setup/{endpoint}", json=payload).status_code == 409
    assert client.post(f"/api/integrations/{endpoint}", json=payload).status_code == 401


@pytest.mark.parametrize("url", [
    "http://169.254.169.254/latest/meta-data", "http://localhost:8000", "file:///tmp/model",
    "http://user:password@localhost:1235/v1", "http://localhost:1235/v1?secret=value",
    "http://localhost:1235/v1#fragment", "http://localhost:1235/admin",
])
def test_gateway_rejects_unauthorized_destinations(url):
    with pytest.raises(ValueError):
        validate_ai_url("lmstudio", url)


def test_gateway_allows_explicit_origin_and_normalizes_path(monkeypatch):
    monkeypatch.setattr(settings(), "ai_allowed_origins", "http://gateway.test:9000")
    assert validate_ai_url("lmstudio", "http://gateway.test:9000") == "http://gateway.test:9000/v1"


def test_invalid_gateway_does_not_change_settings(client, db):
    save_settings(db, {"lm_studio_model": "keep-model"})
    result = client.put("/api/integrations/settings", json={
        "lm_studio_base_url": "http://169.254.169.254", "lm_studio_model": "replace-model",
    })
    assert result.status_code == 422
    assert get_app_setting("lm_studio_model", db=db) == "keep-model"


def test_partial_settings_preserve_other_domains(client, db):
    save_settings(db, {
        "ai_provider": "ollama", "ollama_model": "keep-model", "telegram_bot_username": "keep_bot",
        "telegram_bot_token": "123456:keep-token", "brapi_token": "keep-brapi",
    })
    assert client.put("/api/integrations/settings", json={"poll_seconds": 90}).status_code == 200
    assert client.put("/api/integrations/settings", json={"lm_studio_model": "new-model"}).status_code == 200
    assert client.put("/api/integrations/settings", json={"telegram_bot_token": ""}).status_code == 200
    assert get_app_setting("ai_provider", db=db) == "ollama"
    assert get_app_setting("ollama_model", db=db) == "keep-model"
    assert get_app_setting("telegram_bot_token", db=db) == "123456:keep-token"
    assert get_app_setting("telegram_bot_username", db=db) == "keep_bot"
    assert get_app_setting("brapi_token", db=db) == "keep-brapi"


def test_demo_blocks_dispatch_and_outbound_probes(client, db, monkeypatch):
    document = pending_document(db)
    monkeypatch.setattr(settings(), "demo_mode", True)
    def forbidden(*args, **kwargs):
        pytest.fail("Demonstração não pode consultar serviços reais")
    monkeypatch.setattr(queue, "sync_pending_documents", forbidden)
    monkeypatch.setattr(httpx, "Client", forbidden)
    assert client.post("/api/queue/dispatch").json()["count"] == 0
    assert client.post("/api/integrations/test-ai", json={"url": "http://localhost:1235/v1"}).json()["ok"] is False
    assert client.post("/api/integrations/test-telegram", json={"token": "123456:fake"}).json()["ok"] is False
    assert document.status == "pending"


def test_custody_never_replaces_acquisition_cost(client, db):
    asset = Asset(ticker="TEST3", quantity=2, average_price=15)
    db.add(asset)
    db.commit()
    result = client.post("/api/assets/import-b3", data={"update_average_price": "true"}, files={
        "file": ("posicao.xlsx", custody_xlsx()),
    })
    assert result.status_code == 200
    db.refresh(asset)
    assert asset.quantity == 10
    assert asset.average_price == 15


def test_fully_sold_position_updates_to_zero(client, db):
    asset = Asset(ticker="TEST3", quantity=10, average_price=15)
    db.add(asset)
    db.commit()
    content = (
        "Entrada/Saída;Data;Movimentação;Produto;Quantidade;Preço unitário;Valor da Operação\n"
        "Debito;02/10/2026;Venda;TEST3 - EMPRESA FICTICIA S/A;10;20;200\n"
        "Credito;01/10/2026;Compra;TEST3 - EMPRESA FICTICIA S/A;10;15;150\n"
    )
    result = client.post("/api/assets/import-b3", files={"file": ("mov.csv", content.encode())})
    assert result.status_code == 200
    db.refresh(asset)
    assert asset.quantity == 0


def test_cancel_survives_sync_and_history_cleanup(db):
    document = pending_document(db)
    job = db.scalar(select(ProcessingJob).where(ProcessingJob.target_id == str(document.id)))
    queue.cancel_job(db, job.id)
    assert document.status == "cancelled"
    queue.sync_pending_documents(db)
    assert len(db.scalars(select(ProcessingJob)).all()) == 1
    queue.clear_completed_jobs(db)
    queue.sync_pending_documents(db)
    assert not db.scalars(select(ProcessingJob)).all()


@pytest.mark.parametrize("clear_history", [False, True])
def test_cancel_during_generation_discards_result_and_notification(db, monkeypatch, clear_history):
    document = pending_document(db)
    save_settings(db, {"lm_studio_model": "test-model"})
    def generate(*args, **kwargs):
        job = db.scalar(select(ProcessingJob).where(ProcessingJob.status == "running"))
        queue.cancel_job(db, job.id)
        if clear_history:
            queue.clear_completed_jobs(db)
        return {"facts": [{"fact": "Receita fictícia informada.", "evidence": SOURCE}],
                "risks": [], "interpretations": [], "missing": []}
    monkeypatch.setattr("app.services.documents.complete_json", generate)
    queue.dispatch_queue(db)
    db.refresh(document)
    assert document.status == "cancelled"
    assert document.summary is None
    assert not db.scalar(select(Notification).where(Notification.event_key == f"summary:{document.id}"))
    if clear_history:
        assert db.scalar(select(ProcessingJob)) is None
    else:
        assert db.scalar(select(ProcessingJob)).status == "cancelled"


def test_resource_slots_enforce_limit_and_release_after_error(db):
    save_settings(db, {"max_ai_concurrency": "1"})
    with pytest.raises(RuntimeError):
        with resource_slot(db, "ai", 60) as first:
            assert first
            with resource_slot(db, "ai", 60) as second:
                assert second is None
            raise RuntimeError("erro simulado")
    with resource_slot(db, "ai", 60) as recovered:
        assert recovered


def test_reducing_limit_waits_for_existing_slots(db):
    save_settings(db, {"max_api_concurrency": "2"})
    with resource_slot(db, "api", 60):
        with resource_slot(db, "api", 60):
            save_settings(db, {"max_api_concurrency": "1"})
            with resource_slot(db, "api", 60) as blocked:
                assert blocked is None


def test_changing_timeout_does_not_reclaim_live_execution(db):
    with resource_slot(db, "ai", 600) as token:
        job = queue.enqueue_job(db, job_type="mock_job")
        job.status, job.execution_token, job.started_at = "running", token, utcnow() - timedelta(seconds=120)
        db.commit()
        queue._cleanup_stale_jobs(db, timeout_seconds=30)
        db.refresh(job)
        assert job.status == "running"
    queue._cleanup_stale_jobs(db, timeout_seconds=30)
    db.refresh(job)
    assert job.status == "failed"


def test_api_collector_obeys_shared_limit(db, monkeypatch):
    from app.services.providers import collect_quotes
    save_settings(db, {"max_api_concurrency": "1"})
    def forbidden(*args, **kwargs):
        pytest.fail("Coletor sem slot não pode abrir cliente HTTP")
    monkeypatch.setattr("app.services.providers.open_http_client", forbidden)
    with resource_slot(db, "api", 60):
        assert collect_quotes(db) == 0


def test_concurrent_dispatchers_execute_same_job_once(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'queue.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    with sessions() as db:
        save_settings(db, {"max_ai_concurrency": "2"})
        job_id = queue.enqueue_job(db, job_type="mock_job").id
    barrier = threading.Barrier(2)
    original = queue.resource_slot
    @contextmanager
    def synchronized_slot(*args, **kwargs):
        barrier.wait(timeout=5)
        with original(*args, **kwargs) as token:
            yield token
    monkeypatch.setattr(queue, "resource_slot", synchronized_slot)
    def dispatch():
        with sessions() as db:
            return queue.dispatch_queue(db)
    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: dispatch(), range(2)))
        assert sum(len(result) for result in results) == 1
        with sessions() as db:
            assert db.get(ProcessingJob, job_id).attempts == 1
            assert db.get(ProcessingJob, job_id).status == "completed"
            assert not db.scalars(select(ResourceLease)).all()
    finally:
        engine.dispose()


def test_ai_deadline_cancels_request(monkeypatch):
    cancelled = []
    async def slow_gateway(request):
        try:
            await asyncio.sleep(5)
        finally:
            cancelled.append(True)
        return httpx.Response(200)
    original_client = httpx.AsyncClient
    monkeypatch.setattr(ai.httpx, "AsyncClient", lambda **kwargs: original_client(
        **kwargs, transport=httpx.MockTransport(slow_gateway),
    ))
    with pytest.raises(httpx.ReadTimeout):
        ai.complete_json([], timeout=0.02)
    assert cancelled == [True]


def test_queue_timeout_is_passed_to_generation(db, monkeypatch):
    pending_document(db)
    save_settings(db, {"lm_studio_model": "test-model", "ai_job_timeout_seconds": "30"})
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 30
        raise httpx.ReadTimeout("simulado")
    monkeypatch.setattr("app.services.documents.complete_json", timeout)
    assert queue.dispatch_queue(db)[0]["success"] is False
    assert db.scalar(select(ProcessingJob)).status == "failed"
    assert not db.scalars(select(ResourceLease)).all()


def test_history_carries_quote_from_before_selected_window(db):
    from app.services.portfolio import portfolio_history
    assets = [Asset(ticker="TEST3", quantity=10, average_price=10), Asset(ticker="MOCK4", quantity=10, average_price=10)]
    db.add_all(assets)
    db.commit()
    now = utcnow()
    db.add_all([
        Quote(asset_id=assets[0].id, price=10, source="mock", quoted_at=now - timedelta(days=1)),
        Quote(asset_id=assets[1].id, price=10, source="mock", quoted_at=now - timedelta(days=8)),
    ])
    db.commit()
    point = portfolio_history(db, days=7)[0]
    assert point["total"] == 200
    assert point["gain"] == 0
    assert point["partial"] is False
    assert point["estimated"] is True


def test_history_missing_quotes_are_unknown_instead_of_losses(db):
    from app.services.portfolio import portfolio_history
    assets = [Asset(ticker="TEST3", quantity=10, average_price=10), Asset(ticker="MOCK4", quantity=10, average_price=10)]
    db.add_all(assets)
    db.commit()
    db.add(Quote(asset_id=assets[0].id, price=10, source="mock", quoted_at=utcnow()))
    db.commit()
    point = portfolio_history(db)[0]
    assert point["total"] is None
    assert point["gain"] is None
    assert point["gain_pct"] is None
    assert point["missing_positions"] == ["MOCK4"]


@pytest.mark.parametrize("days", [-1, 0, 401])
def test_history_period_is_bounded(client, days):
    assert client.get(f"/api/portfolio/history?days={days}").status_code == 422


def test_poll_interval_changes_without_restarting_beat(db, monkeypatch):
    from app import tasks
    now = utcnow()
    calls = []
    monkeypatch.setattr(tasks, "locked", lambda name, fn: fn(db))
    monkeypatch.setattr(tasks, "collect_quotes", lambda db: calls.append(True) or 1)
    monkeypatch.setattr(tasks, "utcnow", lambda: now)
    save_settings(db, {"poll_seconds": "120"})
    tasks.poll_market()
    now += timedelta(seconds=60)
    tasks.poll_market()
    assert len(calls) == 1
    save_settings(db, {"poll_seconds": "30"})
    tasks.poll_market()
    assert len(calls) == 2
    tasks.poll_market(force=True)
    assert len(calls) == 3
    assert tasks.celery.conf.beat_schedule["quotes"]["schedule"] == 10


def test_queue_and_market_settings_share_poll_interval(client, db):
    assert client.put("/api/integrations/settings", json={"poll_seconds": 90}).status_code == 200
    assert client.get("/api/queue").json()["settings"]["api_poll_interval_seconds"] == 90
    assert client.post("/api/queue/settings", json={"api_poll_interval_seconds": 60}).status_code == 200
    assert client.get("/api/integrations").json()["poll_seconds"] == 60

"""Gateway único de IA; não faz fallback entre provedores ou envia dados à nuvem."""

import json
from typing import Annotated
import httpx
from pydantic import BaseModel, ConfigDict, Field
from ..config import settings


class GatewayError(ValueError):
    """Erro de configuração seguro para exibição, sem corpo/URL/token do provedor."""


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fact: str
    evidence: str


class SummaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    facts: Annotated[list[Evidence], Field(min_length=1, max_length=12)]
    risks: list[Evidence]
    interpretations: list[str]
    missing: list[str]


def lm_headers():
    return {"Authorization": f"Bearer {settings().lm_studio_api_key}"} if settings().lm_studio_api_key else {}


def complete_json(messages, client=None):
    config = settings()
    own_client = client is None
    client = client or httpx.Client(timeout=config.ai_timeout_seconds)
    try:
        if config.ai_provider == "lmstudio":
            response = client.post(
                f"{config.lm_studio_base_url.rstrip('/')}/chat/completions",
                headers=lm_headers(),
                json={
                    "model": config.lm_studio_model,
                    "messages": messages,
                    "stream": False,
                    "temperature": 0,
                    "max_tokens": 3500,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "financial_summary",
                            "strict": True,
                            "schema": SummaryPayload.model_json_schema(),
                        },
                    },
                },
            )
            response.raise_for_status()
            choice = response.json()["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise ValueError("Resposta incompleta ou recusada pelo gateway de IA")
            content = choice["message"]["content"]
        else:
            response = client.post(
                f"{config.ollama_url.rstrip('/')}/api/chat",
                json={
                    "model": config.ollama_model,
                    "stream": False,
                    "format": SummaryPayload.model_json_schema(),
                    "options": {"temperature": 0},
                    "messages": messages,
                },
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("done_reason") == "length":
                raise ValueError("Resposta truncada pelo provedor de IA")
            content = payload["message"]["content"]
        # Validação local é necessária mesmo com structured output habilitado no servidor.
        return SummaryPayload.model_validate(json.loads(content)).model_dump()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        provider = "LM Studio" if config.ai_provider == "lmstudio" else "Ollama"
        if status in (401, 403):
            raise GatewayError(
                f"{provider} recusou a autenticação. Confira o token e as permissões no servidor."
            ) from None
        if "failed to load model" in exc.response.text.lower():
            raise GatewayError(
                f"{provider} não conseguiu carregar o modelo configurado. Carregue-o no servidor e confira memória, arquivos do modelo e logs antes de tentar novamente."
            ) from None
        raise GatewayError(
            f"{provider} recusou a geração (HTTP {status}). Confira o modelo, o tamanho do contexto e o suporte a JSON estruturado."
        ) from None
    finally:
        if own_client:
            client.close()


def available_models(client=None):
    config = settings()
    own_client = client is None
    client = client or httpx.Client(timeout=10)
    try:
        if config.ai_provider == "lmstudio":
            response = client.get(f"{config.lm_studio_base_url.rstrip('/')}/models", headers=lm_headers())
            response.raise_for_status()
            return [item["id"] for item in response.json()["data"] if isinstance(item.get("id"), str)]
        response = client.get(f"{config.ollama_url.rstrip('/')}/api/tags")
        response.raise_for_status()
        return [item["name"] for item in response.json()["models"] if isinstance(item.get("name"), str)]
    finally:
        if own_client:
            client.close()

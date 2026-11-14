"""Gateway único de IA; não faz fallback entre provedores ou envia dados à nuvem."""

import json
import asyncio
from typing import Annotated
import httpx
from pydantic import BaseModel, ConfigDict, Field
from ..config import settings
from .settings import get_app_setting, validate_ai_url


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


async def _post_with_deadline(url, timeout, options):
    async with httpx.AsyncClient(timeout=timeout, trust_env=False, follow_redirects=False) as client:
        try:
            return await asyncio.wait_for(client.post(url, **options), timeout=timeout)
        except TimeoutError:
            raise httpx.ReadTimeout("Tempo limite total da geração excedido") from None


def _post(client, url, timeout, **options):
    if client is not None:
        return client.post(url, timeout=timeout, **options)
    return asyncio.run(_post_with_deadline(url, timeout, options))


def complete_json(messages, client=None, db=None, timeout=None):
    if settings().demo_mode:
        raise GatewayError("Demonstração não envia documentos a gateways reais.")
    ai_provider = get_app_setting("ai_provider", settings().ai_provider, db=db)
    timeout_raw = get_app_setting("ai_timeout_seconds", str(settings().ai_timeout_seconds), db=db)
    timeout = min(int(timeout_raw), timeout) if timeout is not None else int(timeout_raw)
    try:
        if ai_provider == "lmstudio":
            base_url = get_app_setting("lm_studio_base_url", settings().lm_studio_base_url, db=db)
            base_url = validate_ai_url("lmstudio", base_url)
            model = get_app_setting("lm_studio_model", settings().lm_studio_model, db=db)
            api_key = get_app_setting("lm_studio_api_key", settings().lm_studio_api_key, db=db)
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            response = _post(
                client,
                f"{base_url.rstrip('/')}/chat/completions",
                timeout,
                headers=headers,
                json={
                    "model": model,
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
            base_url = get_app_setting("ollama_url", settings().ollama_url, db=db)
            base_url = validate_ai_url("ollama", base_url)
            model = get_app_setting("ollama_model", settings().ollama_model, db=db)
            response = _post(
                client,
                f"{base_url.rstrip('/')}/api/chat",
                timeout,
                json={
                    "model": model,
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
        provider = "LM Studio" if ai_provider == "lmstudio" else "Ollama"
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


def available_models(client=None, db=None):
    if settings().demo_mode:
        raise GatewayError("Demonstração não consulta gateways reais.")
    ai_provider = get_app_setting("ai_provider", settings().ai_provider, db=db)
    own_client = client is None
    client = client or httpx.Client(timeout=10, trust_env=False, follow_redirects=False)
    try:
        if ai_provider == "lmstudio":
            base_url = get_app_setting("lm_studio_base_url", settings().lm_studio_base_url, db=db)
            base_url = validate_ai_url("lmstudio", base_url)
            api_key = get_app_setting("lm_studio_api_key", settings().lm_studio_api_key, db=db)
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            response = client.get(f"{base_url.rstrip('/')}/models", headers=headers)
            response.raise_for_status()
            return [item["id"] for item in response.json()["data"] if isinstance(item.get("id"), str)]
        base_url = get_app_setting("ollama_url", settings().ollama_url, db=db)
        base_url = validate_ai_url("ollama", base_url)
        response = client.get(f"{base_url.rstrip('/')}/api/tags")
        response.raise_for_status()
        return [item["name"] for item in response.json()["models"] if isinstance(item.get("name"), str)]
    finally:
        if own_client:
            client.close()

import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import httpx
from sqlalchemy import select
from ..config import settings
from ..db import SessionLocal
from ..models import SystemSetting

DEFAULT_SETTINGS = {
    "telegram_bot_token": "",
    "telegram_bot_username": "",
    "brapi_token": "",
    "poll_seconds": "120",
    "ai_provider": "lmstudio",
    "lm_studio_base_url": "http://host.docker.internal:1235/v1",
    "lm_studio_model": "qwen3.5-9b",
    "lm_studio_api_key": "",
    "ai_timeout_seconds": "180",
    "ollama_url": "http://host.docker.internal:11434",
    "ollama_model": "",
    "max_ai_concurrency": "1",
    "max_api_concurrency": "2",
    "ai_queue_paused": "false",
    "ai_job_timeout_seconds": "120",
}


def get_app_setting(key: str, default: str | None = None, db=None) -> str:
    """Retorna configuração com precedência do banco de dados sobre variáveis de ambiente."""
    if db is not None:
        row = db.get(SystemSetting, key)
        if row is not None and row.value is not None:
            return row.value
    else:
        try:
            with SessionLocal() as session:
                row = session.get(SystemSetting, key)
                if row is not None and row.value is not None:
                    return row.value
        except Exception:
            pass

    env_val = getattr(settings(), key, None)
    if env_val is not None:
        return str(env_val)
    if default is not None:
        return default
    return DEFAULT_SETTINGS.get(key, "")


def get_all_settings(db) -> dict[str, str]:
    """Retorna todas as configurações do sistema consolidadas."""
    db_rows = {s.key: s.value for s in db.scalars(select(SystemSetting)).all()}
    res = {}
    for k, def_val in DEFAULT_SETTINGS.items():
        if k in db_rows and db_rows[k] is not None:
            res[k] = db_rows[k]
        else:
            env_val = getattr(settings(), k, None)
            res[k] = str(env_val) if env_val is not None else def_val
    return res


def save_settings(db, new_settings: dict[str, str]) -> None:
    """Grava as configurações no banco de dados."""
    for k, v in new_settings.items():
        val = str(v) if v is not None else ""
        row = db.get(SystemSetting, k)
        if row:
            row.value = val
        else:
            db.add(SystemSetting(key=k, value=val))
    db.commit()


def test_telegram_token_live(token: str) -> dict:
    """Valida um bot token diretamente com a API do Telegram."""
    if settings().demo_mode:
        return {"ok": False, "error": "Demonstração não consulta integrações reais."}
    if not token or ":" not in token:
        return {"ok": False, "error": "Formato de token inválido. O token deve seguir o formato 123456789:ABCdef..."}
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramMoney/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("ok"):
                res = data.get("result", {})
                return {
                    "ok": True,
                    "username": res.get("username", ""),
                    "first_name": res.get("first_name", ""),
                    "message": f"Bot validado com sucesso: @{res.get('username')}",
                }
    except urllib.error.HTTPError as e:
        if e.code in (401, 404):
            return {"ok": False, "error": "Token não autorizado pelo Telegram. Verifique no @BotFather."}
        return {"ok": False, "error": f"Erro HTTP {e.code} da API do Telegram."}
    except Exception:
        return {"ok": False, "error": "Não foi possível conectar à API do Telegram."}
    return {"ok": False, "error": "Resposta inesperada da API do Telegram."}


def validate_ai_url(provider: str, url: str) -> str:
    """Restringe gateways às origens autorizadas na configuração do servidor."""
    value = url.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Informe uma URL HTTP(S) de gateway sem credenciais na URL.")
    if parsed.query or parsed.fragment or parsed.path not in ("", "/v1"):
        raise ValueError("A URL do gateway não aceita query, fragmento ou caminho personalizado.")
    origin = (parsed.scheme, parsed.hostname.lower(), parsed.port or (443 if parsed.scheme == "https" else 80))
    defaults = [
        f"http://{host}:{port}"
        for host in ("localhost", "127.0.0.1", "[::1]", "host.docker.internal")
        for port in ((1234, 1235) if provider == "lmstudio" else (11434,))
    ]
    configured = settings().lm_studio_base_url if provider == "lmstudio" else settings().ollama_url
    allowed = defaults + [configured] + settings().ai_allowed_origins.split(",")
    allowed_origins = set()
    for candidate in allowed:
        item = urlsplit(candidate.strip())
        if item.hostname:
            allowed_origins.add((item.scheme, item.hostname.lower(), item.port or (443 if item.scheme == "https" else 80)))
    if origin not in allowed_origins:
        raise ValueError("Origem do gateway não autorizada. Configure AI_ALLOWED_ORIGINS no servidor.")
    if provider == "ollama" and parsed.path:
        raise ValueError("A URL do Ollama deve conter somente a origem, sem /v1.")
    return value + ("/v1" if provider == "lmstudio" and not parsed.path else "")


def test_ai_endpoint_live(provider: str, url: str, api_key: str = "") -> dict:
    """Testa a conectividade com o gateway de IA e retorna a lista de modelos disponíveis."""
    if settings().demo_mode:
        return {"ok": False, "error": "Demonstração não consulta integrações reais.", "models": []}
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        url = validate_ai_url(provider, url)
        with httpx.Client(timeout=5, follow_redirects=False, trust_env=False) as client:
            if provider == "ollama":
                res = client.get(f"{url}/api/tags")
                res.raise_for_status()
                models = [m.get("name") for m in res.json().get("models", []) if m.get("name")]
            else:
                res = client.get(f"{url}/models", headers=headers)
                res.raise_for_status()
                models = [m.get("id") for m in res.json().get("data", []) if m.get("id")]
        return {
            "ok": True,
            "models": models,
            "message": f"Conexão bem-sucedida! {len(models)} modelo(s) encontrado(s)."
            if models
            else "Gateway acessível, mas nenhum modelo foi encontrado carregado.",
        }
    except ValueError as error:
        return {"ok": False, "error": str(error), "models": []}
    except Exception:
        return {"ok": False, "error": "Não foi possível consultar o gateway de IA. Confira endereço, token e servidor.", "models": []}

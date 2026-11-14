from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, text
from ..auth import create_session, current_owner, hash_password
from ..config import settings
from ..crud import audit, rows
from ..db import get_db
from ..models import AuditLog, Owner
from ..schemas import AITestInput, SetupInput, TelegramTestInput
from ..services.settings import save_settings, test_ai_endpoint_live, test_telegram_token_live, validate_ai_url

router = APIRouter(tags=["system"])


def require_initial_setup(db=Depends(get_db)):
    if db.scalar(select(Owner.id)):
        raise HTTPException(409, "O sistema já foi configurado. Use os testes autenticados nas configurações.")


@router.get("/health")
def health(db=Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "version": "0.1.0"}


@router.get("/api/setup")
def setup(db=Depends(get_db)):
    return {"configured": bool(db.scalar(select(Owner.id))), "demo": settings().demo_mode}


@router.post("/api/setup")
def complete_setup(payload: SetupInput, response: Response, db=Depends(get_db)):
    if db.scalar(select(Owner.id)):
        raise HTTPException(409, "O sistema já foi configurado.")
    if not payload.email or "@" not in payload.email or any(c in payload.email for c in "\r\n#='\""):
        raise HTTPException(422, "Informe um e-mail válido.")
    if len(payload.password) < 12:
        raise HTTPException(422, "A senha deve ter pelo menos 12 caracteres.")
    if any(c in payload.password for c in "\r\n'"):
        raise HTTPException(422, "A senha não aceita aspas simples ou quebras de linha.")
    try:
        lm_url = validate_ai_url("lmstudio", payload.lm_studio_base_url)
        ollama_url = validate_ai_url("ollama", payload.ollama_url)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None

    owner = Owner(
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        timezone=payload.timezone or "America/Sao_Paulo",
    )
    db.add(owner)
    db.flush()

    settings_dict = {
        "telegram_bot_token": payload.telegram_bot_token or "",
        "telegram_bot_username": payload.telegram_bot_username.lstrip("@") or "",
        "brapi_token": payload.brapi_token or "",
        "poll_seconds": str(payload.poll_seconds or 120),
        "ai_provider": payload.ai_provider or "lmstudio",
        "lm_studio_base_url": lm_url,
        "lm_studio_model": payload.lm_studio_model,
        "lm_studio_api_key": payload.lm_studio_api_key or "",
        "ai_timeout_seconds": str(payload.ai_timeout_seconds or 180),
        "ollama_url": ollama_url,
        "ollama_model": payload.ollama_model or "",
    }
    save_settings(db, settings_dict)

    token = create_session(db, owner)
    response.set_cookie(
        "tm_session",
        token,
        httponly=True,
        secure=settings().cookie_secure,
        samesite="strict",
        max_age=43200,
        path="/",
    )
    audit(db, "system.setup", f"Setup inicial realizado para {owner.email}")
    db.commit()
    return {"ok": True, "email": owner.email, "message": "Ambiente e credenciais configurados com sucesso."}


@router.post("/api/setup/test-telegram", dependencies=[Depends(require_initial_setup)])
def test_telegram_setup(payload: TelegramTestInput):
    return test_telegram_token_live(payload.token)


@router.post("/api/setup/test-ai", dependencies=[Depends(require_initial_setup)])
def test_ai_setup(payload: AITestInput):
    return test_ai_endpoint_live(payload.provider, payload.url, payload.api_key)


@router.get("/api/audit")
def audit_log(owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(rows(db, AuditLog, 100))

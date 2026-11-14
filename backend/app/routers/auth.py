from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from ..auth import create_session, current_owner, digest, verify_password
from ..config import settings
from ..crud import audit
from ..db import aware, get_db, utcnow
from ..models import AuthSession, LoginAttempt, Owner
from ..schemas import Login, Preferences

router = APIRouter(tags=["auth"])


@router.post("/api/auth/login")
def login(data: Login, request: Request, response: Response, db=Depends(get_db)):
    key = digest(request.client.host if request.client else "unknown")
    attempt = db.get(LoginAttempt, key)
    now = utcnow()
    if not attempt:
        attempt = LoginAttempt(key=key, attempts=0, window_start=now)
        db.add(attempt)
    if now - aware(attempt.window_start) > timedelta(minutes=15):
        attempt.attempts, attempt.window_start = 0, now
    if attempt.attempts >= 10:
        raise HTTPException(429, "Muitas tentativas. Aguarde 15 minutos.")
    attempt.attempts += 1
    db.commit()
    owner = db.scalar(select(Owner).where(Owner.email == data.email.lower()))
    # Hash fictício mantém custo semelhante para e-mails inexistentes.
    stored = owner.password_hash if owner else "0" * 32 + "$" + "0" * 64
    valid = verify_password(data.password, stored)
    if not owner or not valid:
        raise HTTPException(401, "E-mail ou senha inválidos")
    attempt.attempts = 0
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
    audit(db, "auth.login", "Login do proprietário")
    db.commit()
    return {"email": owner.email}


@router.post("/api/auth/logout")
def logout(request: Request, response: Response, owner=Depends(current_owner), db=Depends(get_db)):
    db.execute(
        delete(AuthSession).where(AuthSession.token_hash == digest(request.cookies.get("tm_session", "")))
    )
    db.commit()
    response.delete_cookie("tm_session", path="/")
    return {"ok": True}


@router.get("/api/me")
def me(owner=Depends(current_owner)):
    return {
        "email": owner.email,
        "telegram_connected": bool(owner.chat_id),
        "telegram_name": owner.telegram_name,
        **{key: getattr(owner, key) for key in Preferences.model_fields},
    }


@router.put("/api/preferences")
def preferences(data: Preferences, owner=Depends(current_owner), db=Depends(get_db)):
    for key, value in data.model_dump().items():
        setattr(owner, key, value)
    audit(db, "preferences.update", "Preferências de notificação atualizadas")
    db.commit()
    return {"ok": True}

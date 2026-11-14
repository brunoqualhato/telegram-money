import hashlib
import hmac
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from .config import settings
from .db import aware, get_db, utcnow
from .models import AuthSession, Owner


def digest(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password: str):
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600_000).hex()
    return f"{salt}${derived}"


def verify_password(password: str, stored: str):
    salt, expected = stored.split("$", 1)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600_000).hex()
    return hmac.compare_digest(actual, expected)


def bootstrap_owner(db):
    if db.scalar(select(Owner)) or not settings().owner_password:
        return
    if len(settings().owner_password) < 12:
        raise RuntimeError("OWNER_PASSWORD precisa ter pelo menos 12 caracteres")
    db.add(
        Owner(
            email=settings().owner_email.lower(),
            password_hash=hash_password(settings().owner_password),
            timezone=settings().timezone,
        )
    )
    db.commit()


def current_owner(request: Request, db=Depends(get_db)):
    token = request.cookies.get("tm_session")
    session = db.get(AuthSession, digest(token)) if token else None
    if not session or aware(session.expires_at) <= utcnow():
        raise HTTPException(401, "Entre para acessar o painel")
    owner = db.get(Owner, session.owner_id)
    if not owner:
        raise HTTPException(401, "Sessão inválida")
    return owner


def create_session(db, owner):
    token = secrets.token_urlsafe(32)
    db.add(
        AuthSession(token_hash=digest(token), owner_id=owner.id, expires_at=utcnow() + timedelta(hours=12))
    )
    db.commit()
    return token

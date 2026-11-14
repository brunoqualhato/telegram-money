"""Slots com aquisição atômica no banco, compartilhados pela API e workers."""
from contextlib import contextmanager
from datetime import timedelta
from functools import wraps
import secrets
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from ..config import settings
from ..db import utcnow
from ..models import ResourceLease
from .settings import get_app_setting


@contextmanager
def resource_slot(db, category, seconds):
    limit = int(get_app_setting(f"max_{category}_concurrency", "1" if category == "ai" else "2", db=db))
    token = secrets.token_hex(24)
    lease_name = None
    active = db.scalar(select(func.count()).select_from(ResourceLease).where(
        ResourceLease.name.like(f"{category}:%"), ResourceLease.expires_at > utcnow(),
    ))
    insert = sqlite_insert if db.bind.dialect.name == "sqlite" else pg_insert
    for slot in range(limit if active < limit else 0):
        name = f"{category}:{slot}"
        now = utcnow()
        stmt = insert(ResourceLease).values(name=name, token=token, expires_at=now + timedelta(seconds=seconds))
        stmt = stmt.on_conflict_do_update(
            index_elements=[ResourceLease.name],
            set_={"token": token, "expires_at": now + timedelta(seconds=seconds)},
            where=ResourceLease.expires_at <= now,
        ).returning(ResourceLease.token)
        acquired = db.scalar(stmt)
        db.commit()
        if acquired:
            lease_name = name
            break
    try:
        yield token if lease_name else None
    finally:
        if lease_name:
            db.rollback()
            db.execute(delete(ResourceLease).where(ResourceLease.name == lease_name, ResourceLease.token == token))
            db.commit()


def limited_api(function):
    @wraps(function)
    def collect(db, *args, **kwargs):
        if settings().demo_mode:
            return 0
        # Cada coletor usa HTTP sequencial; um slot limita uma requisição externa por vez.
        with resource_slot(db, "api", 3600) as token:
            if not token:
                return 0
            return function(db, *args, **kwargs)
    return collect

from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings


def utcnow():
    return datetime.now(timezone.utc)


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class Base(DeclarativeBase):
    pass


url = settings().database_url
if url.startswith("sqlite:///./"):
    Path(url.removeprefix("sqlite:///./")).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(
    url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}, pool_pre_ping=True
)
if url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db

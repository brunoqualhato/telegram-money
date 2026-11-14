import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["OWNER_PASSWORD"] = ""
os.environ["DEMO_MODE"] = "false"
os.environ["APP_ORIGIN"] = "http://localhost:8000"
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:fake-test-token"
os.environ["TELEGRAM_BOT_USERNAME"] = "test_money_bot"
os.environ["AI_PROVIDER"] = "lmstudio"
os.environ["LM_STUDIO_MODEL"] = ""
os.environ["LM_STUDIO_API_KEY"] = ""
os.environ["OLLAMA_MODEL"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.auth import hash_password
from app.db import Base, get_db
from app.main import app
from app.models import Owner


@pytest.fixture
def db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session = sessionmaker(engine, expire_on_commit=False)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def owner(db):
    user = Owner(
        email="owner@example.com",
        password_hash=hash_password("a-strong-test-password"),
        quiet_start=0,
        quiet_end=0,
        chat_id="12345",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def client(db, owner):
    def override():
        yield db

    app.dependency_overrides[get_db] = override
    # Lifespan não abre o banco global; as migrations são testadas separadamente.
    client = TestClient(app, headers={"Origin": "http://localhost:8000"})
    result = client.post("/api/auth/login", json={"email": owner.email, "password": "a-strong-test-password"})
    assert result.status_code == 200
    yield client
    client.close()
    app.dependency_overrides.clear()

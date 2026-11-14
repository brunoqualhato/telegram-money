import pytest
from sqlalchemy import select
from app.models import Owner, SystemSetting
from app.services.settings import get_all_settings, get_app_setting


def test_setup_status_unconfigured(client, db):
    # Remove existing owner
    for o in db.scalars(select(Owner)).all():
        db.delete(o)
    db.commit()

    resp = client.get("/api/setup")
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_setup_wizard_flow(client, db):
    # Remove existing owner
    for o in db.scalars(select(Owner)).all():
        db.delete(o)
    db.commit()

    setup_payload = {
        "email": "novo_admin@example.com",
        "password": "senha-segura-com-mais-de-12-caracteres",
        "timezone": "America/Sao_Paulo",
        "telegram_bot_token": "123456:setup-token",
        "telegram_bot_username": "novo_bot",
        "brapi_token": "setup-brapi-token",
        "poll_seconds": 90,
        "ai_provider": "lmstudio",
        "lm_studio_base_url": "http://localhost:1235/v1",
        "lm_studio_model": "test-model-lm",
        "lm_studio_api_key": "test-key-lm",
        "ai_timeout_seconds": 120,
        "ollama_url": "http://localhost:11434",
        "ollama_model": "",
    }

    # 1. Executa o Setup
    resp = client.post("/api/setup", json=setup_payload)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert "tm_session" in resp.headers.get("set-cookie", "")

    # 2. Verifica se o Owner foi criado no banco
    owner = db.scalar(select(Owner).where(Owner.email == "novo_admin@example.com"))
    assert owner is not None
    assert owner.timezone == "America/Sao_Paulo"

    # 3. Verifica se as configurações foram salvas em system_settings
    settings = get_all_settings(db)
    assert settings["telegram_bot_username"] == "novo_bot"
    assert settings["brapi_token"] == "setup-brapi-token"
    assert settings["poll_seconds"] == "90"
    assert settings["ai_provider"] == "lmstudio"
    assert settings["lm_studio_model"] == "test-model-lm"

    # 4. GET /api/setup agora deve retornar configured: True
    assert client.get("/api/setup").json()["configured"] is True

    # 5. Tentativa de chamar /api/setup novamente deve falhar (409 Conflict)
    resp_again = client.post("/api/setup", json=setup_payload)
    assert resp_again.status_code == 409


def test_integrations_settings_update_and_no_secret_leak(client, db):
    # Atualiza configurações via PUT /api/integrations/settings
    update_payload = {
        "telegram_bot_token": "987654:new-secret-token",
        "telegram_bot_username": "updated_bot",
        "brapi_token": "brapi-new-secret",
        "poll_seconds": 60,
        "ai_provider": "ollama",
        "lm_studio_base_url": "http://localhost:1235/v1",
        "lm_studio_model": "",
        "lm_studio_api_key": "lm-secret-key",
        "ai_timeout_seconds": 180,
        "ollama_url": "http://localhost:11434",
        "ollama_model": "qwen2.5:7b-instruct",
    }
    resp = client.put("/api/integrations/settings", json=update_payload)
    assert resp.status_code == 200

    # Confirma que foram salvas no banco
    assert get_app_setting("telegram_bot_token", db=db) == "987654:new-secret-token"
    assert get_app_setting("brapi_token", db=db) == "brapi-new-secret"
    assert get_app_setting("ai_provider", db=db) == "ollama"

    # Confirma que GET /api/integrations NÃO vaza os segredos
    get_resp = client.get("/api/integrations")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["telegram_configured"] is True
    assert data["telegram_has_token"] is True
    assert data["brapi_has_token"] is True
    assert "987654:new-secret-token" not in str(data)
    assert "brapi-new-secret" not in str(data)
    assert "lm-secret-key" not in str(data)


def test_update_profile(client, owner, db):
    # Atualiza apenas email
    resp = client.put("/api/auth/profile", json={"email": "novo_email@example.com"})
    assert resp.status_code == 200
    db.refresh(owner)
    assert owner.email == "novo_email@example.com"

    # Atualiza senha com senha atual incorreta -> 400
    bad_pass = client.put(
        "/api/auth/profile",
        json={"current_password": "senha_errada", "new_password": "nova-senha-valida-123"},
    )
    assert bad_pass.status_code == 400

    # Atualiza senha com nova senha curta -> 422
    short_pass = client.put(
        "/api/auth/profile",
        json={"current_password": "a-strong-test-password", "new_password": "curta"},
    )
    assert short_pass.status_code == 422

    # Atualiza senha com sucesso
    good_pass = client.put(
        "/api/auth/profile",
        json={"current_password": "a-strong-test-password", "new_password": "nova-senha-valida-123"},
    )
    assert good_pass.status_code == 200

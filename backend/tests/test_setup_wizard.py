from pathlib import Path
import stat
import sys
import pytest

# Adiciona o diretório scripts ao sys.path para importar o setup_wizard
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import setup_wizard


def test_build_env_content():
    cfg = {
        "owner_email": "investidor@example.com",
        "owner_password": "super-secret-password-123",
        "postgres_password": "pg-token-secret-xyz",
        "database_url": "postgresql+psycopg://telegram:pg-token-secret-xyz@db:5432/telegram_money",
        "redis_url": "redis://redis:6379/0",
        "app_origin": "http://localhost:8000",
        "cookie_secure": False,
        "timezone": "America/Sao_Paulo",
        "telegram_bot_token": "123456:abc-token",
        "telegram_bot_username": "my_money_bot",
        "brapi_token": "test-brapi-key",
        "poll_seconds": 60,
        "ai_provider": "lmstudio",
        "lm_studio_base_url": "http://host.docker.internal:1235/v1",
        "lm_studio_model": "qwen3.5-9b",
        "lm_studio_api_key": "",
        "ai_timeout_seconds": 180,
        "ollama_url": "http://localhost:11434",
        "ollama_model": "",
        "demo_mode": False,
        "mode": "docker",
    }
    content = setup_wizard.build_env_content(cfg)
    assert "OWNER_EMAIL='investidor@example.com'" in content
    assert "OWNER_PASSWORD='super-secret-password-123'" in content
    assert "POSTGRES_PASSWORD=pg-token-secret-xyz" in content
    assert "TELEGRAM_BOT_TOKEN=123456:abc-token" in content
    assert "TELEGRAM_BOT_USERNAME=my_money_bot" in content
    assert "BRAPI_TOKEN=test-brapi-key" in content
    assert "POLL_SECONDS=60" in content
    assert "AI_PROVIDER=lmstudio" in content
    assert "LM_STUDIO_MODEL=qwen3.5-9b" in content


def test_parse_existing_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Comentário inicial\n"
        "OWNER_EMAIL='teste@example.com'\n"
        "POLL_SECONDS=90\n"
        "COOKIE_SECURE=true\n"
        "\n"
        "# Outro comentário\n"
        "TELEGRAM_BOT_TOKEN=\"987654:xyz\"\n"
    )
    parsed = setup_wizard.parse_existing_env(env_file)
    assert parsed["OWNER_EMAIL"] == "teste@example.com"
    assert parsed["POLL_SECONDS"] == "90"
    assert parsed["COOKIE_SECURE"] == "true"
    assert parsed["TELEGRAM_BOT_TOKEN"] == "987654:xyz"


def test_telegram_bot_token_format_validation():
    # Token sem dois pontos ou formato inválido
    ok, user, msg = setup_wizard.test_telegram_bot_token("token-invalido")
    assert not ok
    assert "Formato" in msg

    ok, user, msg = setup_wizard.test_telegram_bot_token("")
    assert not ok


def test_brapi_token_empty():
    ok, msg = setup_wizard.test_brapi_token("")
    assert ok
    assert "gratuito" in msg


def test_write_env_file_permissions_and_backup(tmp_path, monkeypatch):
    target = tmp_path / ".env"
    monkeypatch.setattr(setup_wizard, "TARGET_ENV", target)
    monkeypatch.setattr(setup_wizard, "ROOT", tmp_path)

    # 1. Primeira gravação
    setup_wizard.write_env_file("PRIMEIRO_CONTEUDO=1\n")
    assert target.exists()
    assert target.read_text() == "PRIMEIRO_CONTEUDO=1\n"
    # Permissão 0600 em Unix
    file_mode = stat.S_IMODE(target.stat().st_mode)
    assert file_mode == 0o600

    # 2. Segunda gravação gera .env.bak
    setup_wizard.write_env_file("SEGUNDO_CONTEUDO=2\n")
    backup = tmp_path / ".env.bak"
    assert backup.exists()
    assert backup.read_text() == "PRIMEIRO_CONTEUDO=1\n"
    assert target.read_text() == "SEGUNDO_CONTEUDO=2\n"


def test_ollama_selection_is_saved_in_ollama_fields(monkeypatch):
    monkeypatch.setattr(setup_wizard, "discover_lm_studio_models", lambda url: [])
    monkeypatch.setattr(setup_wizard, "discover_ollama_models", lambda url: ["test-model"])
    monkeypatch.setattr(setup_wizard.UI, "ask_choice", lambda *args: "ollama")
    answers = iter(["http://localhost:11434", "chosen-model"])
    monkeypatch.setattr(setup_wizard.UI, "ask", lambda *args: next(answers))
    result = setup_wizard.prompt_ai_step({}, "local")
    assert result["ai_provider"] == "ollama"
    assert result["ollama_url"] == "http://localhost:11434"
    assert result["ollama_model"] == "chosen-model"
    assert result["lm_studio_base_url"] == "http://localhost:1235/v1"


def test_disabling_ai_clears_both_models(monkeypatch):
    monkeypatch.setattr(setup_wizard, "discover_lm_studio_models", lambda url: [])
    monkeypatch.setattr(setup_wizard, "discover_ollama_models", lambda url: [])
    monkeypatch.setattr(setup_wizard.UI, "ask_choice", lambda *args: "none")
    result = setup_wizard.prompt_ai_step({"OLLAMA_MODEL": "old-model"}, "docker")
    assert result["lm_studio_model"] == ""
    assert result["ollama_model"] == ""


def test_quick_defaults_preserve_existing_ai_config():
    result = setup_wizard.ai_defaults({
        "AI_PROVIDER": "ollama", "OLLAMA_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "keep-model", "LM_STUDIO_API_KEY": "keep-test-key",
    }, "local")
    assert result["ai_provider"] == "ollama"
    assert result["ollama_model"] == "keep-model"
    assert result["lm_studio_api_key"] == "keep-test-key"

from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")
    database_url: str = "sqlite:///./data/telegram-money.db"
    redis_url: str = "redis://localhost:6379/0"
    owner_email: str = "voce@example.com"
    owner_password: str = ""
    app_origin: str = "http://localhost:8000"
    cookie_secure: bool = False
    timezone: str = "America/Sao_Paulo"
    telegram_bot_token: str = ""
    telegram_bot_username: str = ""
    brapi_token: str = ""
    poll_seconds: int = Field(default=120, ge=30)
    ai_provider: Literal["lmstudio", "ollama"] = "lmstudio"
    lm_studio_base_url: str = "http://localhost:1235/v1"
    lm_studio_model: str = "qwen3.5-9b"
    lm_studio_api_key: str = ""
    ai_timeout_seconds: int = Field(default=180, ge=5, le=600)
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = ""
    demo_mode: bool = False

    @property
    def ai_model(self):
        return self.lm_studio_model if self.ai_provider == "lmstudio" else self.ollama_model


@lru_cache
def settings():
    return Settings()

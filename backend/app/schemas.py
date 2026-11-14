from datetime import date
from decimal import Decimal
from typing import Literal
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Login(Input):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower()


class AssetInput(Input):
    ticker: str = Field(pattern=r"^[A-Z0-9^][A-Z0-9.^=\-]{0,23}$")
    name: str = Field(default="", max_length=150)
    asset_class: Literal["acao", "fii", "etf", "bdr", "indice", "cripto", "moeda"] = "acao"
    watchlist: str = Field(default="Principal", min_length=1, max_length=80)
    quantity: Decimal = Field(default=Decimal(0), ge=0, le=1_000_000_000)
    average_price: Decimal = Field(default=Decimal(0), ge=0, le=1_000_000_000)

    @field_validator("ticker", mode="before")
    @classmethod
    def upper(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class RuleInput(Input):
    asset_id: int = Field(gt=0)
    kind: Literal["price_above", "price_below", "change_up", "change_down", "high_52w", "low_52w", "abnormal"]
    threshold: Decimal = Field(gt=0, le=1_000_000_000)
    enabled: bool = True


class Preferences(Input):
    notifications_enabled: bool = True
    quiet_start: int = Field(default=22, ge=0, le=23)
    quiet_end: int = Field(default=8, ge=0, le=23)
    max_per_hour: int = Field(default=20, ge=1, le=100)
    timezone: str = "America/Sao_Paulo"
    daily_report: bool = True
    weekly_report: bool = True
    monthly_report: bool = True
    event_alerts: bool = True

    @field_validator("timezone")
    @classmethod
    def timezone_valid(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Fuso horário inválido")
        return value


class EventInput(Input):
    source_id: str = Field(min_length=1, max_length=200)
    ticker: str = Field(pattern=r"^[A-Z0-9][A-Z0-9.\-]{0,23}$")
    kind: Literal[
        "dividendo", "jcp", "rendimento", "amortizacao", "desdobramento", "grupamento", "subscricao"
    ]
    amount: Decimal | None = Field(default=None, ge=0, le=1_000_000_000)
    announced_on: date | None = None
    com_date: date | None = None
    ex_date: date | None = None
    payment_date: date | None = None
    source_url: str = Field(max_length=500)
    status: Literal["confirmed", "cancelled", "estimated"] = "confirmed"

    @field_validator("source_url")
    @classmethod
    def https_only(cls, value):
        if urlparse(value).scheme != "https" or not urlparse(value).hostname:
            raise ValueError("Informe uma URL HTTPS para a fonte original")
        return value


class DocumentInput(Input):
    ticker: str = Field(pattern=r"^[A-Z0-9][A-Z0-9.\-]{0,23}$")
    title: str = Field(min_length=3, max_length=200)
    kind: Literal["relatorio", "fato_relevante", "noticia", "subscricao"] = "relatorio"
    source_url: str = Field(max_length=500)
    text: str = Field(min_length=100, max_length=200_000)
    incomplete: bool = False
    _validate_url = field_validator("source_url")(EventInput.https_only.__func__)


class Toggle(Input):
    enabled: bool

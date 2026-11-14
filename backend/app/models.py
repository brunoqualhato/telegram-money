from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, utcnow


class Owner(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    chat_id: Mapped[str | None] = mapped_column(String(40), unique=True)
    telegram_name: Mapped[str | None] = mapped_column(String(150))
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    quiet_start: Mapped[int] = mapped_column(default=22)
    quiet_end: Mapped[int] = mapped_column(default=8)
    max_per_hour: Mapped[int] = mapped_column(default=20)
    timezone: Mapped[str] = mapped_column(default="America/Sao_Paulo")
    daily_report: Mapped[bool] = mapped_column(default=True)
    weekly_report: Mapped[bool] = mapped_column(default=True)
    monthly_report: Mapped[bool] = mapped_column(default=True)
    event_alerts: Mapped[bool] = mapped_column(default=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int] = mapped_column(default=0)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TelegramLink(Base):
    __tablename__ = "telegram_links"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(24), unique=True)
    name: Mapped[str] = mapped_column(String(150), default="")
    asset_class: Mapped[str] = mapped_column(String(20), default="acao")
    watchlist: Mapped[str] = mapped_column(String(80), default="Principal")
    quantity: Mapped[Decimal] = mapped_column(Numeric(22, 8), default=0)
    average_price: Mapped[Decimal] = mapped_column(Numeric(22, 8), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("asset_id", "quoted_at", "source"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(22, 8))
    change_pct: Mapped[Decimal] = mapped_column(Numeric(16, 6), default=0)
    day_high: Mapped[Decimal | None] = mapped_column(Numeric(22, 8))
    day_low: Mapped[Decimal | None] = mapped_column(Numeric(22, 8))
    high_52w: Mapped[Decimal | None] = mapped_column(Numeric(22, 8))
    low_52w: Mapped[Decimal | None] = mapped_column(Numeric(22, 8))
    currency: Mapped[str] = mapped_column(String(8), default="BRL")
    source: Mapped[str] = mapped_column(String(50), default="brapi")
    quoted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AlertRule(Base):
    __tablename__ = "alert_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    threshold: Mapped[Decimal] = mapped_column(Numeric(22, 8))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    cycle: Mapped[int] = mapped_column(default=0)
    last_triggered: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_key: Mapped[str] = mapped_column(String(200), unique=True)
    category: Mapped[str] = mapped_column(String(30))
    ticker: Mapped[str | None] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(500), default="sistema")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(String(500))
    next_attempt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    telegram_message_id: Mapped[int | None] = mapped_column(Integer)


class CorporateAction(Base):
    __tablename__ = "corporate_actions"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(200), unique=True)
    ticker: Mapped[str] = mapped_column(String(24), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(22, 8))
    announced_on: Mapped[date | None] = mapped_column(Date)
    com_date: Mapped[date | None] = mapped_column(Date)
    ex_date: Mapped[date | None] = mapped_column(Date)
    payment_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    revision: Mapped[int] = mapped_column(default=1)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(24), index=True)
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(30), default="relatorio")
    source_url: Mapped[str] = mapped_column(String(500))
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    text: Mapped[str] = mapped_column(Text)
    incomplete: Mapped[bool] = mapped_column(default=False)
    summary: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MarketReport(Base):
    __tablename__ = "market_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_key: Mapped[str] = mapped_column(String(80), unique=True)
    kind: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProviderState(Base):
    __tablename__ = "provider_states"
    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TreasuryRate(Base):
    __tablename__ = "treasury_rates"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), unique=True)
    maturity: Mapped[str] = mapped_column(String(30))
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    price: Mapped[Decimal] = mapped_column(Numeric(22, 8))
    observed_on: Mapped[date] = mapped_column(Date)
    source_url: Mapped[str] = mapped_column(String(500))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(80))
    detail: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from sqlalchemy import select
from ..db import aware, utcnow
from ..models import AlertRule, Notification, Quote

KINDS = {
    "price_above": "🎯 Preço-alvo atingido",
    "price_below": "🎯 Preço abaixo do alvo",
    "change_up": "🟢 Alerta de alta",
    "change_down": "🔴 Alerta de queda",
    "high_52w": "📈 Máxima de 52 semanas",
    "low_52w": "📉 Mínima de 52 semanas",
    "abnormal": "⚡ Oscilação acima do limite",
}


def latest_quote(db, asset_id):
    return db.scalar(
        select(Quote).where(Quote.asset_id == asset_id).order_by(Quote.quoted_at.desc()).limit(1)
    )


def is_quiet(owner, now=None):
    hour = (now or utcnow()).astimezone(ZoneInfo(owner.timezone)).hour
    start, end = owner.quiet_start, owner.quiet_end
    if start == end:
        return False
    return start <= hour < end if start < end else hour >= start or hour < end


def enqueue(db, event_key, category, title, body, ticker=None, source="sistema"):
    if db.scalar(select(Notification.id).where(Notification.event_key == event_key)):
        return None
    notification = Notification(
        event_key=event_key, category=category, ticker=ticker, title=title, body=body, source=source
    )
    db.add(notification)
    db.flush()
    return notification


def matches(rule, quote):
    threshold = Decimal(rule.threshold)
    conditions = {
        "price_above": lambda: quote.price >= threshold,
        "price_below": lambda: quote.price <= threshold,
        "change_up": lambda: quote.change_pct >= threshold,
        "change_down": lambda: quote.change_pct <= -threshold,
        "abnormal": lambda: abs(quote.change_pct) >= threshold,
        "high_52w": lambda: quote.high_52w is not None and quote.price >= quote.high_52w,
        "low_52w": lambda: quote.low_52w is not None and quote.price <= quote.low_52w,
    }
    return conditions[rule.kind]()


def evaluate_rules(db, asset, quote, now=None):
    now = now or utcnow()
    # Cotações atrasadas são exibidas, mas não disparam novos alertas.
    if now - aware(quote.quoted_at) > timedelta(minutes=15) or aware(quote.quoted_at) > now + timedelta(
        minutes=2
    ):
        return 0
    count = 0
    rules = db.scalars(
        select(AlertRule).where(AlertRule.asset_id == asset.id, AlertRule.enabled.is_(True)).with_for_update()
    ).all()
    for rule in rules:
        condition = matches(rule, quote)
        if not condition:
            rule.triggered = False
            continue
        if rule.triggered:
            continue
        rule.cycle += 1
        rule.triggered = True
        rule.last_triggered = now
        title = f"{KINDS[rule.kind]} · {asset.ticker}"
        body = (
            f"{title}\nCotação: {quote.currency} {quote.price:.2f}\n"
            f"Variação do dia: {quote.change_pct:+.2f}%\nLimite: {rule.threshold:g}\n"
            f"Fonte: {quote.source} · {aware(quote.quoted_at).isoformat()}\nConteúdo informativo."
        )
        if enqueue(db, f"rule:{rule.id}:{rule.cycle}", "price", title, body, asset.ticker, quote.source):
            count += 1
    return count

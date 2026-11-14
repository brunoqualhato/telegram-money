from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from ..db import aware, utcnow
from ..models import CorporateAction, MarketReport, Quote
from .alerts import enqueue
from .portfolio import portfolio_snapshot


def build_report(db, kind="demand", start=None, end=None):
    snapshot = portfolio_snapshot(db)
    labels = {
        "daily": "Fechamento diário",
        "weekly": "Resumo semanal",
        "monthly": "Resumo mensal",
        "demand": "Resumo da carteira",
    }
    now = utcnow()
    lines = [f"📊 {labels[kind]}", f"Gerado em {now:%d/%m/%Y %H:%M} UTC", ""]
    if start:
        lines.append(f"Janela histórica: {start.isoformat()} até {(end or now).isoformat()}")
        lines.append(
            "Posições e custos abaixo são os atuais informados, não uma reconstrução histórica da carteira."
        )
    if snapshot["cost"]:
        lines += [
            f"Patrimônio observado (BRL): R$ {snapshot['total']:.2f}",
            f"Variação contra custo: R$ {snapshot['gain']:+.2f} ({snapshot['gain_pct']:+.2f}%)",
        ]
    for asset in snapshot["assets"]:
        quote = asset["quote"]
        if not quote:
            lines.append(f"{asset['ticker']}: sem cotação")
            continue
        text = (
            f"{asset['ticker']}: {quote['currency']} {quote['price']:.2f} · dia {quote['change_pct']:+.2f}%"
        )
        timestamp = aware(datetime.fromisoformat(quote["quoted_at"]))
        text += f" · fonte {quote['source']} · {timestamp:%d/%m %H:%M} UTC"
        if now - timestamp > timedelta(minutes=15):
            text += " [cotação atrasada]"
        if start:
            baseline = db.scalar(
                select(Quote)
                .where(
                    Quote.asset_id == asset["id"], Quote.quoted_at >= start, Quote.quoted_at < (end or now)
                )
                .order_by(Quote.quoted_at)
                .limit(1)
            )
            closing = db.scalar(
                select(Quote)
                .where(
                    Quote.asset_id == asset["id"], Quote.quoted_at >= start, Quote.quoted_at < (end or now)
                )
                .order_by(Quote.quoted_at.desc())
                .limit(1)
            )
            if (
                baseline
                and closing
                and baseline.price
                and aware(closing.quoted_at) > aware(baseline.quoted_at)
            ):
                change = (closing.price / baseline.price - 1) * 100
                text += f" · preço no período {aware(baseline.quoted_at):%d/%m} a {aware(closing.quoted_at):%d/%m}: {change:+.2f}%"
            else:
                text += " · sem histórico suficiente no período"
        lines.append(text)
    events = db.scalars(
        select(CorporateAction)
        .where(CorporateAction.payment_date >= now.date(), CorporateAction.status == "confirmed")
        .order_by(CorporateAction.payment_date)
        .limit(8)
    ).all()
    if events:
        lines += ["", "Próximos pagamentos (elegibilidade não verificada):"]
        lines += [f"{e.ticker} · {e.payment_date} · {e.amount} por unidade" for e in events]
    lines += ["", snapshot["performance_note"], "Conteúdo informativo; não é recomendação de investimento."]
    return "\n".join(lines)


def create_report(db, kind, key, start=None, end=None):
    existing = db.scalar(select(MarketReport).where(MarketReport.period_key == key))
    if existing:
        return existing
    body = build_report(db, kind, start, end)
    report = MarketReport(kind=kind, period_key=key, body=body)
    db.add(report)
    enqueue(db, f"report:{key}", "report", body.splitlines()[0], body)
    db.commit()
    return report


def scheduled_reports(db, owner, now=None):
    local = (now or utcnow()).astimezone(ZoneInfo(owner.timezone))
    if local.hour < 18 or local.weekday() >= 5:
        return
    if owner.daily_report:
        create_report(db, "daily", f"daily:{local.date()}")
    if owner.weekly_report and local.weekday() == 4:
        week_start = (local - timedelta(days=4)).replace(hour=0, minute=0, second=0, microsecond=0)
        create_report(db, "weekly", f"weekly:{local:%G-%V}", week_start)
    # O mensal fecha no primeiro dia útil do mês seguinte.
    first = local.date().replace(day=1)
    first_business = first + timedelta(days=2 if first.weekday() == 5 else 1 if first.weekday() == 6 else 0)
    if owner.monthly_report and local.date() == first_business:
        previous_end = first - timedelta(days=1)
        start = local.replace(
            year=previous_end.year, month=previous_end.month, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        end = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        create_report(db, "monthly", f"monthly:{previous_end:%Y-%m}", start, end)

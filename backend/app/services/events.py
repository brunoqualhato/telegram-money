from datetime import timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from ..db import utcnow
from ..models import Asset, CorporateAction, Owner
from .alerts import enqueue


def upsert_event(db, data, notify=True):
    values = data.model_dump()
    row = db.scalar(
        select(CorporateAction).where(CorporateAction.source_id == data.source_id).with_for_update()
    )
    changed = row is not None and any(getattr(row, key) != value for key, value in values.items())
    if row and not changed:
        return row, False
    if row:
        for key, value in values.items():
            setattr(row, key, value)
        row.revision += 1
    else:
        row = CorporateAction(**values)
        db.add(row)
    db.flush()
    owner = db.scalar(select(Owner))
    tracked = db.scalar(select(Asset.id).where(Asset.ticker == row.ticker))
    today = utcnow().astimezone(ZoneInfo(owner.timezone if owner else "America/Sao_Paulo")).date()
    relevant = (
        changed
        or (row.announced_on and row.announced_on >= today - timedelta(days=1))
        or (row.payment_date and row.payment_date >= today)
    )
    if notify and owner and owner.event_alerts and tracked and relevant:
        title = f"💰 {'Atualização' if changed else 'Novo evento'} · {row.ticker} · {row.kind}"
        body = (
            f"{title}\nValor por unidade: {row.amount if row.amount is not None else 'não informado'}\n"
            f"Data-com: {row.com_date or 'não informada'}\nPagamento: {row.payment_date or 'não informado'}\n"
            f"Situação: {row.status}\nFonte: {row.source_url}"
        )
        enqueue(db, f"event:{row.id}:v{row.revision}", "event", title, body, row.ticker, row.source_url)
    return row, True


def event_reminders(db, owner, today):
    if not owner.event_alerts:
        return
    tickers = select(Asset.ticker)
    events = db.scalars(
        select(CorporateAction).where(
            CorporateAction.ticker.in_(tickers), CorporateAction.status == "confirmed"
        )
    ).all()
    for event in events:
        for field, label in [("com_date", "Data-com amanhã"), ("payment_date", "Pagamento amanhã")]:
            if getattr(event, field) == today + timedelta(days=1):
                title = f"📅 {label} · {event.ticker}"
                enqueue(
                    db,
                    f"reminder:{event.id}:{field}:{getattr(event, field)}:v{event.revision}",
                    "event",
                    title,
                    f"{title}\n{event.kind} · valor por unidade: {event.amount}\nFonte: {event.source_url}",
                    event.ticker,
                    event.source_url,
                )

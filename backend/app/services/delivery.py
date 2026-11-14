from datetime import timedelta
import httpx
from sqlalchemy import func, select
from ..config import settings
from ..db import utcnow
from ..models import Notification, Owner
from .alerts import is_quiet
from .providers import state
from .settings import get_app_setting


def send_pending(db, client=None):
    owner = db.scalar(select(Owner))
    bot_token = get_app_setting("telegram_bot_token", db=db)
    if (
        settings().demo_mode
        or not bot_token
        or not owner
        or not owner.chat_id
        or not owner.notifications_enabled
        or is_quiet(owner)
    ):
        return 0
    now = utcnow()
    # Entregas abandonadas podem ter chegado ao Telegram antes de uma queda do worker.
    abandoned = db.scalars(
        select(Notification).where(
            Notification.status == "sending", Notification.next_attempt < now - timedelta(minutes=5)
        )
    ).all()
    for item in abandoned:
        item.status, item.error = (
            "uncertain",
            "Worker interrompido durante o envio; confira o Telegram antes de reenviar.",
        )
    db.commit()
    sent = db.scalar(
        select(func.count()).select_from(Notification).where(Notification.sent_at >= now - timedelta(hours=1))
    )
    budget = max(0, owner.max_per_hour - sent)
    own_client = client is None
    client = client or httpx.Client(timeout=20)
    delivered = 0
    try:
        for _ in range(min(budget, 20)):
            item = db.scalar(
                select(Notification)
                .where(Notification.status.in_(["pending", "retry"]), Notification.next_attempt <= utcnow())
                .order_by(Notification.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if not item:
                break
            item.status, item.attempts, item.next_attempt = "sending", item.attempts + 1, utcnow()
            db.commit()
            try:
                response = client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={
                        "chat_id": owner.chat_id,
                        "text": item.body[:4000],
                        "link_preview_options": {"is_disabled": True},
                    },
                )
                payload = response.json()
                if response.status_code == 429:
                    item.status = "retry" if item.attempts < 5 else "failed"
                    delay = max(5, min(int(payload.get("parameters", {}).get("retry_after", 60)), 3600))
                    item.next_attempt = utcnow() + timedelta(seconds=delay)
                    item.error = "Limite do Telegram; aguardando nova tentativa."
                    db.commit()
                    break
                if not response.is_success or not payload.get("ok"):
                    item.status = "failed"
                    item.error = f"Telegram recusou a mensagem (HTTP {response.status_code}); verifique se o bot foi bloqueado."
                else:
                    item.status, item.sent_at, item.error = "sent", utcnow(), None
                    item.telegram_message_id = payload["result"]["message_id"]
                    state(db, "telegram")
                    delivered += 1
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout):
                item.status = "retry" if item.attempts < 5 else "failed"
                item.next_attempt = utcnow() + timedelta(seconds=min(30 * 2**item.attempts, 3600))
                item.error = "Não foi possível conectar ao Telegram."
            except (httpx.HTTPError, ValueError, KeyError):
                item.status = "uncertain"
                item.error = "Resposta inconclusiva. Confira o Telegram antes de reenviar manualmente."
            db.commit()
        return delivered
    finally:
        if own_client:
            client.close()

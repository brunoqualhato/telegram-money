from datetime import timedelta
from zoneinfo import ZoneInfo
from celery import Celery
from celery.schedules import crontab
from redis import Redis
from sqlalchemy import delete, select
from .config import settings
from .db import SessionLocal, utcnow
from .models import AuthSession, Owner, Quote, TelegramLink
from .services.delivery import send_pending
from .services.events import event_reminders
from .services.providers import collect_dividends, collect_news, collect_quotes, collect_treasury
from .services.reports import scheduled_reports
from .services.settings import get_app_setting, save_settings

celery = Celery("telegram_money", broker=settings().redis_url, include=["app.tasks"])
celery.conf.update(
    timezone=settings().timezone,
    task_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    task_ignore_result=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=840,
    task_time_limit=900,
    beat_schedule={
        "quotes": {"task": "market.poll", "schedule": 10.0},
        "deliver": {"task": "notifications.deliver", "schedule": 10.0},
        "events": {"task": "market.events", "schedule": 3600.0},
        "news": {"task": "market.news", "schedule": 3600.0},
        "treasury": {"task": "market.treasury", "schedule": crontab(hour="10,15", minute=10)},
        "reports-reminders": {"task": "reports.tick", "schedule": 60.0},
        "documents": {"task": "documents.pending", "schedule": 30.0},
        "cleanup": {"task": "maintenance.cleanup", "schedule": crontab(hour=3, minute=15)},
    },
)


def locked(name, function):
    if settings().demo_mode:
        return
    redis = Redis.from_url(settings().redis_url)
    # Um único worker pessoal; o lock também protege chamadas concorrentes da API.
    lock = redis.lock(f"telegram-money:{name}", timeout=920, blocking_timeout=0)
    if not lock.acquire(blocking=False):
        return
    try:
        with SessionLocal() as db:
            return function(db)
    finally:
        if lock.owned():
            lock.release()


@celery.task(name="market.poll", expires=120)
def poll_market(force=False):
    def run(db):
        from datetime import datetime
        from .db import aware

        interval = int(get_app_setting("poll_seconds", str(settings().poll_seconds), db=db))
        last = get_app_setting("quotes_last_polled_at", "", db=db)
        now = utcnow()
        if not force and last and (now - aware(datetime.fromisoformat(last))).total_seconds() < interval:
            return 0
        result = collect_quotes(db)
        save_settings(db, {"quotes_last_polled_at": now.isoformat()})
        return result

    return locked("quotes", run)


@celery.task(name="market.events", expires=3600)
def poll_events():
    return locked("events", collect_dividends)


@celery.task(name="market.news", expires=3600)
def poll_news():
    return locked("news", collect_news)


@celery.task(name="market.treasury", expires=3600)
def poll_treasury():
    return locked("treasury", collect_treasury)


@celery.task(name="notifications.deliver", expires=30)
def deliver():
    return locked("delivery", send_pending)


@celery.task(name="documents.pending", expires=60)
def pending_documents():
    def run(db):
        from .services.queue import dispatch_queue

        dispatch_queue(db)

    return locked("documents", run)


@celery.task(name="reports.tick", expires=120)
def reports_tick():
    def run(db):
        owner = db.scalar(select(Owner))
        if owner:
            scheduled_reports(db, owner)
            event_reminders(db, owner, utcnow().astimezone(ZoneInfo(owner.timezone)).date())
            db.commit()

    return locked("reports", run)


@celery.task(name="maintenance.cleanup")
def cleanup():
    with SessionLocal() as db:
        now = utcnow()
        db.execute(delete(Quote).where(Quote.quoted_at < now - timedelta(days=400)))
        db.execute(delete(AuthSession).where(AuthSession.expires_at < now))
        db.execute(delete(TelegramLink).where(TelegramLink.expires_at < now))
        db.commit()

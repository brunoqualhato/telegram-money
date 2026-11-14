from datetime import timedelta
from decimal import Decimal
from sqlalchemy import select
from .auth import hash_password
from .db import utcnow
from .models import AlertRule, Asset, CorporateAction, Notification, Owner, ProcessingJob, Quote


def seed_demo(db):
    if db.scalar(select(Asset.id)):
        return
    if not db.scalar(select(Owner.id)):
        db.add(Owner(email="demo@example.com", password_hash=hash_password("demonstracao-local")))
        db.flush()
    now = utcnow()
    examples = [
        ("PETR4", "Petrobras", "acao", "100", "36.10", "40.12", "1.25"),
        ("VALE3", "Vale", "acao", "80", "75.50", "74.12", "-2.14"),
        ("HGLG11", "Pátria Log", "fii", "30", "151.00", "157.30", "0.84"),
        ("XPML11", "XP Malls", "fii", "50", "102.20", "108.45", "1.12"),
        ("ITUB4", "Itaú Unibanco", "acao", "120", "31.80", "36.72", "0.45"),
        ("BOVA11", "iShares Ibovespa", "etf", "20", "126.00", "133.45", "0.68"),
    ]
    for ticker, name, kind, qty, cost, price, change in examples:
        asset = Asset(
            ticker=ticker,
            name=name,
            asset_class=kind,
            quantity=Decimal(qty),
            average_price=Decimal(cost),
            watchlist="Renda passiva" if kind == "fii" else "Principal",
        )
        db.add(asset)
        db.flush()
        for i in range(31):
            factor = Decimal("0.94") + Decimal(i) * Decimal("0.002") + Decimal((i * 7) % 5 - 2) / 1000
            db.add(
                Quote(
                    asset_id=asset.id,
                    price=Decimal(price) * factor if i < 30 else Decimal(price),
                    change_pct=Decimal(change),
                    source="exemplo ilustrativo",
                    quoted_at=now - timedelta(days=30 - i),
                    day_high=Decimal(price) * Decimal("1.02"),
                    day_low=Decimal(price) * Decimal("0.98"),
                    high_52w=Decimal(price) * Decimal("1.18"),
                    low_52w=Decimal(price) * Decimal("0.8"),
                )
            )
        db.add(AlertRule(asset_id=asset.id, kind="change_down", threshold=Decimal("3")))
    db.add(
        CorporateAction(
            source_id="demo:xpml",
            ticker="XPML11",
            kind="rendimento",
            amount=Decimal("0.92"),
            com_date=(now + timedelta(days=3)).date(),
            payment_date=(now + timedelta(days=14)).date(),
            source_url="https://example.com/exemplo-ilustrativo",
            status="estimated",
        )
    )
    for i, (ticker, title, category) in enumerate(
        [
            ("VALE3", "Alerta de queda", "price"),
            ("XPML11", "Novo rendimento", "event"),
            ("PETR4", "Preço-alvo atingido", "price"),
        ]
    ):
        db.add(
            Notification(
                event_key=f"demo:{i}",
                ticker=ticker,
                title=title,
                category=category,
                body="Exemplo ilustrativo. Esta notificação não foi enviada ao Telegram.",
                source="exemplo ilustrativo",
                status="demo",
                created_at=now - timedelta(minutes=15 * (i + 1)),
            )
        )
    db.add(
        ProcessingJob(
            category="ai",
            job_type="ai_document_summary",
            title="Resumo IA · PETR4 - Fato Relevante (Produção 3T)",
            target_id="1",
            status="completed",
            priority=10,
            created_at=now - timedelta(minutes=45),
            started_at=now - timedelta(minutes=45),
            completed_at=now - timedelta(minutes=44),
        )
    )
    db.add(
        ProcessingJob(
            category="ai",
            job_type="ai_document_summary",
            title="Resumo IA · VALE3 - Relatório de Desempenho",
            target_id="2",
            status="pending",
            priority=0,
            created_at=now - timedelta(minutes=5),
        )
    )
    db.add(
        ProcessingJob(
            category="api",
            job_type="api_quotes_poll",
            title="Coleta de Cotações · B3 & Brapi",
            status="completed",
            priority=0,
            created_at=now - timedelta(minutes=10),
            started_at=now - timedelta(minutes=10),
            completed_at=now - timedelta(minutes=9),
        )
    )
    db.commit()

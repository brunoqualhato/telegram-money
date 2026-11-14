from datetime import timedelta
from decimal import Decimal
import httpx
import pytest
from sqlalchemy import func, select
from app.auth import digest
from app.db import utcnow
from app.models import Asset, Notification, Quote, TelegramLink
from app.services.alerts import enqueue
from app.services.delivery import send_pending
from app.services.documents import validate_summary
from app.services.portfolio import portfolio_snapshot
from app.services.providers import collect_quotes, parse_quote, parse_treasury_csv
from app.services.reports import create_report


def test_quote_parser_requires_real_values_and_time():
    payload = {
        "regularMarketPrice": 40.12,
        "regularMarketChangePercent": 1.25,
        "regularMarketTime": "2026-11-13T19:00:00Z",
    }
    parsed = parse_quote(payload)
    assert parsed["price"] == Decimal("40.12")
    for bad in [None, -1, "NaN", "Infinity"]:
        with pytest.raises((ValueError, KeyError)):
            parse_quote({**payload, "regularMarketPrice": bad})
    with pytest.raises(KeyError):
        parse_quote({"regularMarketPrice": 10, "regularMarketChangePercent": 1})


def test_collection_deduplicates_source_timestamp(db):
    db.add(Asset(ticker="PETR4"))
    db.commit()
    data = {
        "results": [
            {
                "symbol": "PETR4",
                "requestedSymbol": "PETR4",
                "data": {
                    "regularMarketPrice": 40,
                    "regularMarketChangePercent": 1,
                    "regularMarketTime": utcnow().isoformat(),
                },
            }
        ]
    }
    client = httpx.Client(
        base_url="https://brapi.dev", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=data))
    )
    assert collect_quotes(db, client) == 1
    assert collect_quotes(db, client) == 0
    assert db.scalar(select(func.count()).select_from(Quote)) == 1


def test_currency_totals_do_not_mix(db):
    for ticker, currency in [("PETR4", "BRL"), ("AAPL", "USD")]:
        asset = Asset(ticker=ticker, quantity=10, average_price=5)
        db.add(asset)
        db.flush()
        db.add(Quote(asset_id=asset.id, price=10, change_pct=0, currency=currency, quoted_at=utcnow()))
    db.commit()
    result = portfolio_snapshot(db)
    assert result["total"] == 100
    assert result["cost"] == 50
    assert result["missing_positions"] == 1


def test_treasury_uses_latest_date_and_decimal_comma():
    csv = "Tipo Titulo;Data Vencimento;Data Base;Taxa Compra Manha;PU Compra Manha\nTesouro IPCA;15/08/2030;12/11/2026;6,10;3020,30\nTesouro Selic;01/03/2029;13/11/2026;0,05;15123,45\nTesouro Prefixado;01/01/2030;13/11/2026;12,30;700,10\n"
    rows = parse_treasury_csv(csv)
    assert len(rows) == 2
    assert rows[0]["rate"] == Decimal("0.05")
    assert rows[0]["price"] == Decimal("15123.45")


def test_ai_rejects_invented_citations():
    source = "O fundo apresentou receita de R$ 10 milhões no trimestre."
    valid = validate_summary({"facts": [{"fact": "Receita informada.", "evidence": source}]}, source)
    assert len(valid["facts"]) == 1
    with pytest.raises(ValueError):
        validate_summary(
            {"facts": [{"fact": "Receita de 20 milhões.", "evidence": "Receita de R$ 20 milhões"}]}, source
        )


@pytest.mark.parametrize(
    "failure,expected",
    [
        ("ok", "sent"),
        ("connect", "retry"),
        ("read", "uncertain"),
        ("rejected", "failed"),
        ("rate_limit", "retry"),
    ],
)
def test_delivery_records_outcome_and_never_blindly_retries(db, owner, failure, expected):
    enqueue(db, "key", "price", "Título", "Texto")
    db.commit()

    def transport(request):
        if failure == "connect":
            raise httpx.ConnectError("failed", request=request)
        if failure == "read":
            raise httpx.ReadTimeout("timeout", request=request)
        if failure == "rejected":
            return httpx.Response(403, json={"ok": False})
        if failure == "rate_limit":
            return httpx.Response(429, json={"ok": False, "parameters": {"retry_after": 60}})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 42}})

    client = httpx.Client(transport=httpx.MockTransport(transport))
    send_pending(db, client)
    item = db.scalar(select(Notification))
    assert item.status == expected
    assert item.attempts == 1
    if expected == "sent":
        assert item.telegram_message_id == 42
    if expected in ("sent", "uncertain", "failed"):
        assert send_pending(db, client) == 0
        assert item.attempts == 1


def test_pause_and_hourly_limit(db, owner):
    enqueue(db, "pending", "test", "title", "text")
    db.commit()
    owner.notifications_enabled = False
    db.commit()
    assert send_pending(db) == 0
    assert db.scalar(select(Notification)).attempts == 0
    owner.notifications_enabled = True
    owner.max_per_hour = 1
    db.add(
        Notification(
            event_key="sent", category="test", title="sent", body="text", status="sent", sent_at=utcnow()
        )
    )
    db.commit()
    assert send_pending(db) == 0


def test_report_scheduling_is_idempotent(db, owner):
    create_report(db, "daily", "daily:2026-11-13")
    create_report(db, "daily", "daily:2026-11-13")
    assert db.scalar(select(func.count()).select_from(Notification)) == 1


def test_telegram_link_expires_and_consumes_once(db, owner, monkeypatch):
    import app.bot as bot

    class Context:
        def __enter__(self):
            return db

        def __exit__(self, *_):
            pass

    monkeypatch.setattr(bot, "SessionLocal", Context)
    db.add(
        TelegramLink(
            token_hash=digest("valid-token"), owner_id=owner.id, expires_at=utcnow() + timedelta(minutes=1)
        )
    )
    db.add(
        TelegramLink(
            token_hash=digest("expired-token"), owner_id=owner.id, expires_at=utcnow() - timedelta(minutes=1)
        )
    )
    db.commit()
    assert not bot.link_account("expired-token", 999, "test")
    assert bot.link_account("valid-token", 999, "test")
    assert not bot.link_account("valid-token", 111, "other")
    assert owner.chat_id == "999"
    assert "não está vinculado" in bot.command_response(111, "/carteira")
    assert "Resumo da carteira" in bot.command_response(999, "/carteira")


def test_open_news_collection(db):
    from app.models import Document
    from app.services.providers import collect_news

    db.add(Asset(ticker="PETR4"))
    db.commit()

    rss_content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<rss><channel>"
        "<item>"
        "<title>Petrobras registra alta na produção de petróleo</title>"
        "<link>https://example.com/noticia-petrobras</link>"
        "<pubDate>Wed, 13 Nov 2026 12:00:00 GMT</pubDate>"
        "</item>"
        "</channel></rss>"
    )
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, text=rss_content)))
    assert collect_news(db, client=client) == 1
    assert collect_news(db, client=client) == 0
    doc = db.scalar(select(Document).where(Document.ticker == "PETR4"))
    assert doc is not None
    assert doc.kind == "noticia"
    assert "Petrobras" in doc.title


def test_parse_b3_movimentacao_sample():
    from b3_fixtures import movements_xlsx
    from app.services.portfolio import parse_b3_position

    items = parse_b3_position(movements_xlsx(), "movimentacao.xlsx")
    assert len(items) == 1
    assert items[0]["ticker"] == "TEST3"
    assert items[0]["quantity"] == Decimal("15")
    assert items[0]["average_price"] == Decimal("15")
    assert items[0]["asset_class"] == "acao"


def test_parse_b3_movimentacao_csv_calculations():
    from app.services.portfolio import parse_b3_position

    # 1. Compras múltiplas com cálculo do preço médio ponderado
    # 2. Venda parcial preservando preço médio unitário das cotas restantes
    # 3. Transferência interna
    # 4. Desdobro (split) dividindo preço médio proporcionalmente
    csv_data = (
        "Entrada/Saída;Data;Movimentação;Produto;Instituição;Quantidade;Preço unitário;Valor da Operação\n"
        "Credito;01/10/2026;Transferência - Liquidação;VALE3 - VALE S/A;CORRETORA;10;60.00;600.00\n"
        "Credito;05/10/2026;Transferência - Liquidação;VALE3 - VALE S/A;CORRETORA;10;70.00;700.00\n"
        "Debito;10/10/2026;Transferência - Liquidação;VALE3 - VALE S/A;CORRETORA;5;80.00;400.00\n"
        "Credito;15/10/2026;Desdobro;VALE3 - VALE S/A;CORRETORA;15;0.00;0.00\n"
        "Credito;01/10/2026;Transferência - Liquidação;HGLG11 - CSHG LOGÍSTICA FII;CORRETORA;5;160.00;800.00\n"
        "Credito;02/10/2026;Transferência - Liquidação;AAPL34 - APPLE INC BDR;CORRETORA;2;50.00;100.00\n"
    )
    items = parse_b3_position(csv_data.encode("utf-8"), "mov.csv")
    lookup = {it["ticker"]: it for it in items}

    # VALE3:
    # 10 @ 60 = 600
    # + 10 @ 70 = 700 -> 20 @ 65
    # - 5 @ 80 -> 15 restantes @ 65
    # Desdobro +15 -> 30 cotas @ 32.50
    vale = lookup["VALE3"]
    assert vale["quantity"] == Decimal("30")
    assert round(vale["average_price"], 2) == Decimal("32.50")
    assert vale["asset_class"] == "acao"

    hglg = lookup["HGLG11"]
    assert hglg["quantity"] == Decimal("5")
    assert round(hglg["average_price"], 2) == Decimal("160.00")
    assert hglg["asset_class"] == "fii"

    aapl = lookup["AAPL34"]
    assert aapl["quantity"] == Decimal("2")
    assert round(aapl["average_price"], 2) == Decimal("50.00")
    assert aapl["asset_class"] == "bdr"

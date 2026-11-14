from sqlalchemy import select
from app.models import AlertRule, Asset, CorporateAction


def test_private_endpoints_and_csrf(client):
    assert client.get("/api/me").status_code == 200
    assert (
        client.post(
            "/api/assets", headers={"Origin": "https://evil.example"}, json={"ticker": "PETR4"}
        ).status_code
        == 403
    )
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/assets").status_code == 401


def test_crud_assets_rules_portfolio(client, db):
    response = client.post("/api/assets", json={"ticker": "petr4", "quantity": "10", "average_price": "30"})
    assert response.status_code == 201, response.text
    asset_id = response.json()["id"]
    assert response.json()["ticker"] == "PETR4"
    assert client.post("/api/assets", json={"ticker": "PETR4"}).status_code == 409
    assert client.post("/api/assets", json={"ticker": "INVALID/TICKER"}).status_code == 422
    assert client.post("/api/assets", json={"ticker": "VALE3", "quantity": -1}).status_code == 422
    response = client.post("/api/rules", json={"asset_id": asset_id, "kind": "price_above", "threshold": 40})
    assert response.status_code == 201
    rule_id = response.json()["id"]
    assert client.get("/api/rules").json()[0]["ticker"] == "PETR4"
    assert client.patch(f"/api/rules/{rule_id}", json={"enabled": False}).status_code == 200
    assert not db.get(AlertRule, rule_id).enabled
    assert client.get("/api/overview").json()["missing_positions"] == 1
    assert client.delete(f"/api/assets/{asset_id}").status_code == 200
    assert not db.scalar(select(AlertRule))
    assert not db.scalar(select(Asset))


def test_validation_and_no_secret_leak(client):
    result = client.put("/api/preferences", json={"timezone": "invalid/zone"})
    assert result.status_code == 422
    assert (
        client.post("/api/rules", json={"asset_id": 999, "kind": "price_above", "threshold": 40}).status_code
        == 404
    )
    data = client.get("/api/integrations").json()
    assert data["telegram_configured"]
    assert "fake-test-token" not in str(data)
    assert "password_hash" not in str(client.get("/api/me").json())


def test_login_rate_limit(client, owner):
    for _ in range(10):
        assert (
            client.post("/api/auth/login", json={"email": owner.email, "password": "wrong"}).status_code
            == 401
        )
    assert client.post("/api/auth/login", json={"email": owner.email, "password": "wrong"}).status_code == 429


def test_idempotent_event_updates(client, db):
    payload = {
        "source_id": "cvm:123",
        "ticker": "PETR4",
        "kind": "dividendo",
        "amount": "0.92",
        "com_date": "2026-12-01",
        "payment_date": "2026-12-10",
        "source_url": "https://example.com/original",
    }
    initial = client.post("/api/events", json=payload).json()
    repeated = client.post("/api/events", json=payload).json()
    assert initial["id"] == repeated["id"]
    assert not repeated["changed"]
    payload["amount"] = "1.10"
    changed = client.post("/api/events", json=payload).json()
    assert changed["revision"] == 2
    assert len(db.scalars(select(CorporateAction)).all()) == 1
    payload["status"] = "cancelled"
    assert client.post("/api/events", json=payload).json()["revision"] == 3


def test_document_import_and_safety(client):
    payload = {
        "ticker": "HGLG11",
        "title": "Relatório mensal",
        "source_url": "https://example.com/documento",
        "text": "O fundo informou receita e resultados no documento original. " * 5,
    }
    first = client.post("/api/documents", json=payload)
    assert first.status_code == 201, first.text
    assert client.post("/api/documents", json=payload).json()["id"] == first.json()["id"]
    assert "text" not in client.get("/api/documents").json()[0]
    payload["source_url"] = "javascript:alert(1)"
    assert client.post("/api/documents", json=payload).status_code == 422


def test_retry_only_failed_or_uncertain(client, db):
    from app.models import Notification

    item = Notification(event_key="example", category="test", title="test", body="test", status="sent")
    db.add(item)
    db.commit()
    assert client.post(f"/api/notifications/{item.id}/retry").status_code == 409
    item.status = "uncertain"
    db.commit()
    assert client.post(f"/api/notifications/{item.id}/retry").status_code == 200
    assert item.status == "pending"


def test_import_b3_position(client, db):
    from pathlib import Path

    sample = Path("/Users/brunoqualhato/Downloads/posicao-2026-11-13-22-19-05.xlsx")
    if sample.is_file():
        with open(sample, "rb") as f:
            res = client.post(
                "/api/assets/import-b3",
                files={
                    "file": (
                        "posicao.xlsx",
                        f.read(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["imported"] == 25
        assert data["updated"] == 0
        # Second import updates existing
        with open(sample, "rb") as f:
            res2 = client.post(
                "/api/assets/import-b3",
                files={
                    "file": (
                        "posicao.xlsx",
                        f.read(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )
        assert res2.status_code == 200
        assert res2.json()["imported"] == 0
        assert res2.json()["updated"] == 25

    # Test CSV import
    csv_content = (
        "Código de Negociação;Produto;Tipo;Quantidade;Preço de Fechamento\n"
        "ITUB4;ITUB4 - ITAU UNIBANCO;PN;50;35.50\n"
    )
    res_csv = client.post(
        "/api/assets/import-b3",
        files={"file": ("posicao.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert res_csv.status_code == 200
    assert db.scalar(select(Asset).where(Asset.ticker == "ITUB4")).quantity == 50


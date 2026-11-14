from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy import func, select
from app.db import utcnow
from app.models import AlertRule, Asset, Notification, Quote
from app.services.alerts import evaluate_rules, is_quiet, matches


def make_asset(db):
    asset = Asset(ticker="PETR4", quantity=10, average_price=30)
    db.add(asset)
    db.flush()
    return asset


def test_crossing_deduplicates_and_rearms(db):
    asset = make_asset(db)
    rule = AlertRule(asset_id=asset.id, kind="price_above", threshold=40)
    db.add(rule)
    db.flush()

    def evaluate(price):
        quote = Quote(asset_id=asset.id, price=Decimal(price), change_pct=Decimal("1"), quoted_at=utcnow())
        return evaluate_rules(db, asset, quote)

    assert evaluate("39") == 0
    assert evaluate("40") == 1
    assert evaluate("41") == 0
    assert evaluate("41") == 0
    assert evaluate("39") == 0
    assert evaluate("40") == 1
    assert db.scalar(select(func.count()).select_from(Notification)) == 2
    assert rule.cycle == 2


def test_stale_or_future_quotes_do_not_trigger(db):
    asset = make_asset(db)
    rule = AlertRule(asset_id=asset.id, kind="price_above", threshold=40)
    db.add(rule)
    db.flush()
    for timestamp in [utcnow() - timedelta(hours=1), utcnow() + timedelta(hours=1)]:
        quote = Quote(asset_id=asset.id, price=Decimal(42), change_pct=Decimal(2), quoted_at=timestamp)
        assert evaluate_rules(db, asset, quote) == 0
    assert not rule.triggered


@pytest.mark.parametrize(
    "kind,price,change,threshold,expected",
    [
        ("price_below", 39, 0, 40, True),
        ("price_above", 39, 0, 40, False),
        ("change_up", 40, 3, 2, True),
        ("change_down", 40, -3, 2, True),
        ("change_down", 40, 3, 2, False),
        ("abnormal", 40, -4, 3, True),
        ("high_52w", 50, 0, 1, True),
        ("low_52w", 30, 0, 1, True),
    ],
)
def test_rule_conditions(kind, price, change, threshold, expected):
    rule = AlertRule(kind=kind, threshold=Decimal(threshold))
    quote = Quote(price=Decimal(price), change_pct=Decimal(change), high_52w=Decimal(50), low_52w=Decimal(30))
    assert matches(rule, quote) == expected


@pytest.mark.parametrize("hour,quiet", [(0, True), (7, True), (8, False), (21, False), (22, True)])
def test_quiet_hours_overnight(owner, hour, quiet):
    owner.quiet_start, owner.quiet_end, owner.timezone = 22, 8, "UTC"
    assert is_quiet(owner, datetime(2026, 1, 1, hour, tzinfo=timezone.utc)) == quiet


def test_equal_quiet_hours_disable_silence(owner):
    owner.quiet_start = owner.quiet_end = 8
    assert not is_quiet(owner)

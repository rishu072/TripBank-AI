import pytest

from app.errors import AppError
from app.money import from_value, to_value
from app.schemas import CATEGORIES
from app.services import budget
from app.services.payments import verify_payload


def order(amount=1000, currency="USD"):
    return {"provider_order_id": "PP1", "amount": amount, "currency": currency}


def payload(value="10.00", currency="USD", status="COMPLETED", oid="PP1"):
    return {
        "id": oid,
        "status": status,
        "purchase_units": [{"payments": {"captures": [{"id": "CAP1", "status": "COMPLETED", "amount": {"currency_code": currency, "value": value}}]}}],
    }


def test_money_roundtrip():
    assert to_value(123456) == "1234.56"
    assert to_value(5) == "0.05"
    assert from_value("1234.56") == 123456


def test_money_rejects_bad_values():
    for bad in ("12.345", "-1.00", "abc"):
        with pytest.raises(AppError):
            from_value(bad)


def test_verify_accepts_exact_match():
    assert verify_payload(order(), payload()) == "CAP1"


def test_verify_rejects_amount_currency_and_reference():
    for p in (payload("10.01"), payload(currency="EUR"), payload(oid="OTHER")):
        with pytest.raises(AppError) as e:
            verify_payload(order(), p)
        assert e.value.code == "CAPTURE_MISMATCH"


def test_verify_rejects_incomplete():
    with pytest.raises(AppError) as e:
        verify_payload(order(), payload(status="APPROVED"))
    assert e.value.code == "ORDER_NOT_APPROVED"


def test_allocate_sums_to_total():
    for total in (1, 99999, 5000000, 7777777):
        assert sum(budget.allocate(total, budget.DEFAULT_PCT).values()) == total


def test_parse_plan_validates_shares():
    shares = [{"category": c, "percent": p, "explanation": "x"} for c, p in budget.DEFAULT_PCT.items()]
    plan = budget.parse_plan({"shares": shares, "assumptions": ["a"], "confidence": "high"}, 1000000)
    assert sum(c["amount"] for c in plan["categories"]) == 1000000
    shares[0]["percent"] += 1
    with pytest.raises(AppError):
        budget.parse_plan({"shares": shares, "assumptions": [], "confidence": "high"}, 1000000)
    assert [c["category"] for c in plan["categories"]] == CATEGORIES

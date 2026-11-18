"""Focused tests of the active OOP logic manager; no live AI access."""
from datetime import date, timedelta

from classes.logicManagerClass import logicManager

TODAY = date(2026, 11, 18)


def product(days=2, category="Dairy & Eggs", quantity=10):
    return {
        "product_name": "Milk",
        "category": category,
        "quantity_in_stock": quantity,
        "expiry_date": (TODAY + timedelta(days=days)).isoformat(),
        "current_price": 5.0,
    }


def assessment(risk="high", discount=40, unsold=8):
    return {
        "status": "ok", "risk_level": risk,
        "recommended_discount_percent": discount,
        "predicted_unsold_quantity": unsold,
    }


def test_expired_items_never_discounted():
    manager = logicManager()
    result = manager.evaluate(product(days=-1), assessment(), TODAY)
    assert result["outcome"] == "EXPIRED"
    assert result["discount_percent"] == 0


def test_ai_failure_routes_to_manual_review():
    manager = logicManager()
    result = manager.evaluate(product(), {"status": "failed"}, TODAY)
    assert result["outcome"] == "MANUAL_REVIEW"


def test_urgent_uses_ai_risk_and_unsold_quantity():
    manager = logicManager()
    result = manager.evaluate(product(), assessment(), TODAY)
    assert result["outcome"] == "URGENT_DISCOUNT"
    assert result["discount_percent"] == 40


def test_category_configuration_overrides_ai():
    manager = logicManager()
    manager.load_categories([product()])
    manager.set_category_discount("Dairy & Eggs", 15)
    result = manager.evaluate(product(), assessment(), TODAY)
    assert result["discount_percent"] == 15


def test_discount_above_configured_cap_is_limited():
    manager = logicManager()
    manager.set_max_discount(25)
    result = manager.evaluate(product(), assessment(discount=90), TODAY)
    assert result["discount_percent"] == 25


def test_expired_overrides_category_configuration():
    manager = logicManager()
    manager.load_categories([product()])
    manager.set_category_discount("Dairy & Eggs", 35)
    result = manager.evaluate(product(days=-2), assessment(), TODAY)
    assert result["discount_percent"] == 0

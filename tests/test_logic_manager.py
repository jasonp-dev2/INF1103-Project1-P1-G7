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


def test_category_cap_limits_ai_recommendation():
    manager = logicManager()
    manager.load_categories([product()])
    manager.set_category_discount_cap("Dairy & Eggs", 15)
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
    manager.set_category_discount_cap("Dairy & Eggs", 35)
    result = manager.evaluate(product(days=-2), assessment(), TODAY)
    assert result["discount_percent"] == 0

def test_category_cap_does_not_raise_ai_recommendation():
    manager = logicManager()
    manager.set_max_discount(80)
    manager.set_category_discount_cap("Meat & Seafood", 70)
    result = manager.evaluate(product(category="Meat & Seafood", days=5),
                              assessment(risk="medium", discount=20), TODAY)
    assert result["discount_percent"] == 20


def test_meat_category_cap_at_70():
    manager = logicManager()
    manager.set_max_discount(80)
    manager.set_category_discount_cap("Meat & Seafood", 70)
    result = manager.evaluate(product(category="Meat & Seafood", days=5),
                              assessment(risk="medium", discount=85), TODAY)
    assert result["discount_percent"] == 70
    assert result["needs_staff_approval"] is True


def test_global_cap_remains_upper_bound():
    manager = logicManager()
    manager.set_category_discount_cap("Meat & Seafood", 70)
    result = manager.evaluate(product(category="Meat & Seafood", days=5),
                              assessment(risk="medium", discount=85), TODAY)
    assert result["discount_percent"] == 50


def test_zero_category_cap_blocks_discount():
    manager = logicManager()
    manager.set_category_discount_cap("Dairy & Eggs", 0)
    result = manager.evaluate(product(days=5),
                              assessment(risk="medium", discount=40), TODAY)
    assert result["discount_percent"] == 0
    assert not result["needs_staff_approval"]


def test_low_risk_does_not_get_forced_category_discount():
    manager = logicManager()
    manager.set_max_discount(80)
    manager.set_category_discount_cap("Dairy & Eggs", 70)
    result = manager.evaluate(product(days=5),
                              assessment(risk="low", discount=25), TODAY)
    assert result["discount_percent"] == 0


def test_failed_ai_is_not_replaced_by_category_cap():
    manager = logicManager()
    manager.set_max_discount(80)
    manager.set_category_discount_cap("Dairy & Eggs", 70)
    result = manager.evaluate(product(days=5), {"status": "failed"}, TODAY)
    assert result["outcome"] == "MANUAL_REVIEW"
    assert result["discount_percent"] == 0


def test_category_settings_round_trip_and_reset():
    manager = logicManager()
    manager.set_max_discount(80)
    manager.set_category_discount_cap("Meat & Seafood", 70)
    saved = manager.get_settings()
    restored = logicManager()
    restored.load_settings(saved)
    assert restored.get_settings() == saved
    restored.remove_category_discount_cap("Meat & Seafood")
    assert "meat & seafood" not in restored.get_category_discount_caps()

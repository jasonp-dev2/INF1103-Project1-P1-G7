"""
Tests for logic_manager.py.
These tests use hardcoded sample AI responses, so they never call the
real AI and need no API key or internet.
Run them with:  python -m pytest
"""
from datetime import date, timedelta

import logic_manager

TODAY = date(2026, 10, 10)

# ---------------------------------------------------------------------------
# Helpers that build sample data
# ---------------------------------------------------------------------------

def make_product(days_left: int, quantity: int = 10, price: float = 5.00) -> dict:
    """A sample product that expires 'days_left' days after TODAY."""
    expiry = TODAY + timedelta(days=days_left)
    return {
        "product_name": "Milk",
        "category": "Dairy & Eggs",
        "quantity_in_stock": quantity,
        "expiry_date": str(expiry),
        "current_price": price,
    }


def make_ai(risk: str, discount: int, unsold: int) -> dict:
    """A sample AI response that worked (hardcoded, not from the real AI)."""
    return {
        "status": "ok",
        "risk_level": risk,
        "recommended_discount_percent": discount,
        "predicted_unsold_quantity": unsold,
    }


AI_FAILED = {"status": "failed", "error": "Gemini service could not be reached."}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def test_days_until_expiry_future():
    assert logic_manager.days_until_expiry("2026-10-15", TODAY) == 5


def test_days_until_expiry_expired_is_negative():
    assert logic_manager.days_until_expiry("2026-10-05", TODAY) == -5


def test_calculate_final_price():
    # 20% off $10.00 is $8.00
    assert logic_manager.calculate_final_price(10.00, 20) == 8.00


def test_apply_discount_cap_limits_high_and_negative():
    assert logic_manager.apply_discount_cap(80, 50) == 50
    assert logic_manager.apply_discount_cap(-10, 50) == 0
    assert logic_manager.apply_discount_cap(20, 50) == 20


def test_unsold_ratio_with_zero_quantity_does_not_crash():
    assert logic_manager.calculate_unsold_ratio(3, 0) == 0


# ---------------------------------------------------------------------------
# R1: expired products are never discounted
# ---------------------------------------------------------------------------

def test_r1_expired_product():
    decision = logic_manager.evaluate(make_product(-9), make_ai("high", 30, 8), TODAY)
    assert decision["rule"] == "R1"
    assert decision["outcome"] == "EXPIRED"
    assert decision["discount_percent"] == 0


# ---------------------------------------------------------------------------
# R2: products that are not near expiry get no discount
# ---------------------------------------------------------------------------

def test_r2_not_near_expiry():
    decision = logic_manager.evaluate(make_product(8), make_ai("high", 30, 8), TODAY)
    assert decision["rule"] == "R2"
    assert decision["discount_percent"] == 0


def test_r2_boundary_exactly_7_days_is_near_expiry():
    decision = logic_manager.evaluate(make_product(7), make_ai("medium", 20, 3), TODAY)
    assert decision["rule"] != "R2"


# ---------------------------------------------------------------------------
# R3: AI failure goes to manual review
# ---------------------------------------------------------------------------

def test_r3_ai_failed_goes_to_manual_review():
    decision = logic_manager.evaluate(make_product(2), AI_FAILED, TODAY)
    assert decision["rule"] == "R3"
    assert decision["outcome"] == "MANUAL_REVIEW"
    assert decision["discount_percent"] == 0


# ---------------------------------------------------------------------------
# R4: urgent discount (multi-condition rule using AI output)
#     days_left <= 3 AND risk is high AND unsold ratio >= 0.5
# ---------------------------------------------------------------------------

def test_r4_urgent_discount_when_all_conditions_met():
    decision = logic_manager.evaluate(make_product(2), make_ai("high", 40, 8), TODAY)
    assert decision["rule"] == "R4"
    assert decision["outcome"] == "URGENT_DISCOUNT"
    assert decision["discount_percent"] == 40
    assert decision["needs_staff_approval"] is True


def test_r4_boundary_exactly_3_days_and_exactly_half_unsold():
    decision = logic_manager.evaluate(make_product(3), make_ai("high", 40, 5), TODAY)
    assert decision["rule"] == "R4"


def test_r4_not_applied_when_4_days_left():
    decision = logic_manager.evaluate(make_product(4), make_ai("high", 40, 8), TODAY)
    assert decision["rule"] == "R5"


def test_r4_not_applied_when_less_than_half_unsold():
    decision = logic_manager.evaluate(make_product(2), make_ai("high", 40, 4), TODAY)
    assert decision["rule"] == "R5"


def test_r4_not_applied_when_risk_is_medium():
    decision = logic_manager.evaluate(make_product(2), make_ai("medium", 40, 8), TODAY)
    assert decision["rule"] == "R5"


def test_r4_raises_small_discount_to_minimum_30():
    decision = logic_manager.evaluate(make_product(2), make_ai("high", 10, 8), TODAY)
    assert decision["rule"] == "R4"
    assert decision["discount_percent"] == 30


def test_r4_discount_is_capped_at_50():
    decision = logic_manager.evaluate(make_product(2), make_ai("high", 80, 8), TODAY)
    assert decision["discount_percent"] == 50


# ---------------------------------------------------------------------------
# R5: normal discount (AI suggests a discount and risk is not low)
# ---------------------------------------------------------------------------

def test_r5_normal_discount():
    decision = logic_manager.evaluate(make_product(5), make_ai("medium", 20, 3),
                                      TODAY)
    assert decision["rule"] == "R5"
    assert decision["outcome"] == "DISCOUNT_RECOMMENDED"
    assert decision["discount_percent"] == 20
    assert decision["final_price"] == 4.00        # 20% off $5.00
    assert decision["needs_staff_approval"] is True


def test_r5_discount_is_capped_at_50():
    decision = logic_manager.evaluate(make_product(5), make_ai("medium", 80, 3),
                                      TODAY)
    assert decision["discount_percent"] == 50


def test_r5_not_applied_when_risk_is_low():
    decision = logic_manager.evaluate(make_product(5), make_ai("low", 20, 1), TODAY)
    assert decision["rule"] == "R6"


def test_r5_not_applied_when_ai_suggests_no_discount():
    decision = logic_manager.evaluate(make_product(5), make_ai("medium", 0, 1), TODAY)
    assert decision["rule"] == "R6"


# ---------------------------------------------------------------------------
# R6: monitor, no discount
# ---------------------------------------------------------------------------

def test_r6_monitor_has_no_discount_and_no_approval():
    decision = logic_manager.evaluate(make_product(5), make_ai("low", 0, 0), TODAY)
    assert decision["rule"] == "R6"
    assert decision["outcome"] == "MONITOR"
    assert decision["discount_percent"] == 0
    assert decision["needs_staff_approval"] is False


# ---------------------------------------------------------------------------
# Waste cost
# ---------------------------------------------------------------------------

def test_waste_cost_is_unsold_units_times_price():
    # 8 unsold units x $5.00 = $40.00
    decision = logic_manager.evaluate(make_product(2), make_ai("high", 40, 8), TODAY)
    assert decision["waste_cost_if_unsold"] == 40.00

# ---------------------------------------------------------------------------
# Direct tests of the remaining helper functions
# ---------------------------------------------------------------------------

def test_calculate_waste_cost():
    # 3 unsold units x $10.00 = $30.00
    assert logic_manager.calculate_waste_cost(3, 10.00) == 30.00


def test_make_decision_builds_complete_dictionary():
    decision = logic_manager.make_decision(
        "DISCOUNT_RECOMMENDED", "R5", "Test reason.", 5, 20, 10.00, 4.00)
    assert decision["final_price"] == 8.00           # 20% off $10.00
    assert decision["needs_staff_approval"] is True  # a discount needs approval
    assert decision["rule"] == "R5"


# ---------------------------------------------------------------------------
# Rule priority: the first rule that matches wins
# ---------------------------------------------------------------------------

def test_r1_wins_over_ai_failure():
    decision = logic_manager.evaluate(make_product(-3), AI_FAILED, TODAY)
    assert decision["rule"] == "R1"


def test_r2_wins_over_ai_failure():
    decision = logic_manager.evaluate(make_product(20), AI_FAILED, TODAY)
    assert decision["rule"] == "R2"
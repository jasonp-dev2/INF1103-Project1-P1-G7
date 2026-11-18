"""OOP Logic Manager regression tests for configurable discount ceilings."""
import unittest
from datetime import date, timedelta

from classes.logicManagerClass import (
    logicManager,
    OUTCOME_EXPIRED,
    OUTCOME_NOT_NEAR_EXPIRY,
    OUTCOME_MANUAL_REVIEW,
    OUTCOME_URGENT_DISCOUNT,
    OUTCOME_DISCOUNT,
    OUTCOME_MONITOR,
    DEFAULT_OTHERS_DISCOUNT,
)

TODAY = date(2026, 11, 18)


def make_product(category="Meat & Seafood", days=5, quantity=10, price=10.0):
    return {
        "product_name": "Test product",
        "category": category,
        "quantity_in_stock": quantity,
        "expiry_date": (TODAY + timedelta(days=days)).isoformat(),
        "current_price": price,
    }


def make_ai(risk="medium", percent=20, unsold=3):
    return {
        "status": "ok",
        "risk_level": risk,
        "recommended_discount_percent": percent,
        "predicted_unsold_quantity": unsold,
    }


class TestCategoryNormalizing(unittest.TestCase):
    def setUp(self):
        self.logic = logicManager()
        self.logic.load_categories([
            {"category": "Meat"}, {"category": "Berries"},
        ])

    def test_plural_and_case(self):
        self.assertEqual(self.logic.resolve_category("MEATS"), "meat")
        self.assertEqual(self.logic.resolve_category("berries"), "berry")
        self.assertEqual(self.logic.resolve_category("unknown"), "others")

    def test_unknown_uses_other_cap(self):
        self.assertEqual(
            self.logic.get_final_discount(make_product("Hardware"), 50),
            DEFAULT_OTHERS_DISCOUNT,
        )

    def test_categories_are_not_changed_by_cap_setting(self):
        self.logic.set_category_discount_cap("Meat & Seafood", 70)
        self.assertIn("meat & seafood", self.logic.get_category_discount_caps())


class TestDiscountCaps(unittest.TestCase):
    def setUp(self):
        self.logic = logicManager()

    def test_70_percent_category_cap_does_not_force_70(self):
        self.logic.set_max_discount(80)
        self.logic.set_category_discount_cap("Meat & Seafood", 70)
        self.assertEqual(
            self.logic.get_final_discount(make_product(), 20), 20
        )

    def test_85_percent_ai_is_capped_at_70(self):
        self.logic.set_max_discount(80)
        self.logic.set_category_discount_cap("Meat & Seafood", 70)
        self.assertEqual(
            self.logic.get_final_discount(make_product(), 85), 70
        )

    def test_global_50_still_limits_category_70(self):
        self.logic.set_category_discount_cap("Meat & Seafood", 70)
        self.assertEqual(
            self.logic.get_final_discount(make_product(), 85), 50
        )

    def test_zero_cap_blocks_discount(self):
        self.logic.set_category_discount_cap("Meat & Seafood", 0)
        self.assertEqual(
            self.logic.get_final_discount(make_product(), 85), 0
        )

    def test_invalid_caps(self):
        for cap in (-1, 101, "70", True):
            with self.subTest(cap=cap):
                with self.assertRaises(ValueError):
                    self.logic.set_category_discount_cap("Meat", cap)

    def test_invalid_global_cap(self):
        with self.assertRaises(ValueError):
            self.logic.set_max_discount(105)

    def test_reset_category_cap(self):
        self.logic.set_category_discount_cap("Meat & Seafood", 70)
        self.logic.remove_category_discount_cap("Meat & Seafood")
        self.assertNotIn(
            "meat & seafood", self.logic.get_category_discount_caps()
        )

    def test_save_load_settings(self):
        self.logic.set_max_discount(80)
        self.logic.set_category_discount_cap("Meat & Seafood", 70)
        new_logic = logicManager()
        new_logic.load_settings(self.logic.get_settings())
        self.assertEqual(new_logic.get_settings(), self.logic.get_settings())

    def test_load_old_settings_key_for_migration(self):
        self.logic.load_settings({
            "max_discount": 80,
            "category_discounts": {"Meat & Seafood": 70},
        })
        self.assertEqual(
            self.logic.get_final_discount(make_product(), 85), 70
        )


class TestRuleOrder(unittest.TestCase):
    def setUp(self):
        self.logic = logicManager()
        self.logic.set_max_discount(80)
        self.logic.set_category_discount_cap("Meat & Seafood", 70)

    def test_expired_never_discounted(self):
        result = self.logic.evaluate(make_product(days=-1), make_ai(), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_EXPIRED)
        self.assertEqual(result["discount_percent"], 0)

    def test_not_near_expiry_never_discounted(self):
        result = self.logic.evaluate(make_product(days=8), make_ai(), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_NOT_NEAR_EXPIRY)
        self.assertEqual(result["discount_percent"], 0)

    def test_failed_ai_goes_to_review(self):
        result = self.logic.evaluate(
            make_product(), {"status": "failed"}, TODAY
        )
        self.assertEqual(result["outcome"], OUTCOME_MANUAL_REVIEW)
        self.assertEqual(result["discount_percent"], 0)

    def test_normal_discount_uses_ai_below_cap(self):
        result = self.logic.evaluate(
            make_product(days=5), make_ai(percent=20), TODAY
        )
        self.assertEqual(result["outcome"], OUTCOME_DISCOUNT)
        self.assertEqual(result["discount_percent"], 20)

    def test_normal_discount_uses_cap_above_limit(self):
        result = self.logic.evaluate(
            make_product(days=5), make_ai(percent=85), TODAY
        )
        self.assertEqual(result["discount_percent"], 70)

    def test_low_risk_still_monitored(self):
        result = self.logic.evaluate(
            make_product(days=5), make_ai(risk="low"), TODAY
        )
        self.assertEqual(result["outcome"], OUTCOME_MONITOR)

    def test_urgent_minimum_is_still_applied(self):
        result = self.logic.evaluate(
            make_product(days=2),
            make_ai(risk="high", percent=10, unsold=8),
            TODAY,
        )
        self.assertEqual(result["outcome"], OUTCOME_URGENT_DISCOUNT)
        self.assertEqual(result["discount_percent"], 30)

    def test_urgent_minimum_obeys_category_cap(self):
        self.logic.set_category_discount_cap("Meat & Seafood", 15)
        result = self.logic.evaluate(
            make_product(days=2),
            make_ai(risk="high", percent=10, unsold=8),
            TODAY,
        )
        self.assertEqual(result["discount_percent"], 15)

    def test_no_approval_when_cap_is_zero(self):
        self.logic.set_category_discount_cap("Meat & Seafood", 0)
        result = self.logic.evaluate(
            make_product(days=5), make_ai(), TODAY
        )
        self.assertFalse(result["needs_staff_approval"])


if __name__ == "__main__":
    unittest.main()

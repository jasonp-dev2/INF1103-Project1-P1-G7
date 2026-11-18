import unittest
from datetime import date, timedelta

from classes.logicManagerClass import (
    logicManager,
    OUTCOME_EXPIRED, OUTCOME_NOT_NEAR_EXPIRY, OUTCOME_MANUAL_REVIEW,
    OUTCOME_URGENT_DISCOUNT, OUTCOME_DISCOUNT, OUTCOME_MONITOR,
    MAX_DISCOUNT_PERCENT, DEFAULT_OTHERS_DISCOUNT, OTHERS_CATEGORY,
)

TODAY = date(2026, 11, 17)


def make_product(category="Meat", days_left=5, price=10.0, quantity=10):
    expiry = TODAY + timedelta(days=days_left)
    return {
        "category": category,
        "expiry_date": expiry.strftime("%Y-%m-%d"),
        "current_price": price,
        "quantity_in_stock": quantity,
    }


def make_ai(risk="medium", percent=15, unsold=3, status="ok"):
    return {
        "status": status,
        "risk_level": risk,
        "recommended_discount_percent": percent,
        "predicted_unsold_quantity": unsold,
    }


def new_manager():
    lm = logicManager()
    # Categories that exist in the "database"
    lm.load_categories([{"category": "Meat"}, {"category": "Berries"}, {"category": "Cheese"}])
    return lm


class TestCategoryNormalizing(unittest.TestCase):
    def setUp(self):
        self.lm = new_manager()

    def test_plurals_and_case(self):
        self.assertEqual(self.lm._normalize_category("Meats"), "meat")
        self.assertEqual(self.lm._normalize_category("  MEAT  "), "meat")
        self.assertEqual(self.lm._normalize_category("berries"), "berry")
        self.assertEqual(self.lm._normalize_category("cheeses"), "cheese")
        self.assertEqual(self.lm._normalize_category("juices"), "juice")
        self.assertEqual(self.lm._normalize_category("tomatoes"), "tomato")

    def test_extra_spaces_inside(self):
        self.assertEqual(self.lm._normalize_category("duck   meats"), "duck meat")

    def test_other_and_others_are_same(self):
        self.assertEqual(self.lm._normalize_category("other"), OTHERS_CATEGORY)
        self.assertEqual(self.lm._normalize_category("Others"), OTHERS_CATEGORY)

    def test_empty_or_none(self):
        self.assertEqual(self.lm._normalize_category(""), "")
        self.assertEqual(self.lm._normalize_category(None), "")


class TestResolveCategory(unittest.TestCase):
    def test_known_category(self):
        lm = new_manager()
        self.assertEqual(lm.resolve_category("meats"), "meat")
        self.assertEqual(lm.resolve_category("Berries"), "berry")

    def test_unknown_category_goes_to_others(self):
        lm = new_manager()
        self.assertEqual(lm.resolve_category("meet"), OTHERS_CATEGORY)
        self.assertEqual(lm.resolve_category("Hardware"), OTHERS_CATEGORY)

    def test_missing_category_goes_to_others(self):
        lm = new_manager()
        self.assertEqual(lm.resolve_category(None), OTHERS_CATEGORY)
        self.assertEqual(lm.resolve_category(""), OTHERS_CATEGORY)

    def test_before_categories_loaded_not_everything_is_others(self):
        lm = logicManager()   # load_categories() never called
        self.assertEqual(lm.resolve_category("meats"), "meat")


class TestMaxDiscount(unittest.TestCase):
    def setUp(self):
        self.lm = new_manager()

    def test_default(self):
        self.assertEqual(self.lm.get_max_discount(), MAX_DISCOUNT_PERCENT)

    def test_set_valid(self):
        self.lm.set_max_discount(70)
        self.assertEqual(self.lm.get_max_discount(), 70)

    def test_set_boundaries(self):
        self.lm.set_max_discount(0)
        self.lm.set_max_discount(100)

    def test_set_invalid(self):
        with self.assertRaises(ValueError):
            self.lm.set_max_discount(-1)
        with self.assertRaises(ValueError):
            self.lm.set_max_discount(101)


class TestCategoryDiscount(unittest.TestCase):
    def setUp(self):
        self.lm = new_manager()

    def test_returns_real_bucket(self):
        self.assertEqual(self.lm.set_category_discount("Meats", 40), "meat")
        self.assertEqual(self.lm.get_category_discounts()["meat"], 40)

    def test_unknown_category_saved_under_others(self):
        self.assertEqual(self.lm.set_category_discount("meet", 25), OTHERS_CATEGORY)
        self.assertEqual(self.lm.get_category_discounts()[OTHERS_CATEGORY], 25)
        self.assertNotIn("meet", self.lm.get_category_discounts())

    def test_others_has_default(self):
        self.assertEqual(self.lm.get_category_discounts()[OTHERS_CATEGORY], DEFAULT_OTHERS_DISCOUNT)

    def test_invalid_values(self):
        with self.assertRaises(ValueError):
            self.lm.set_category_discount("meat", -5)
        with self.assertRaises(ValueError):
            self.lm.set_category_discount("meat", 101)
        with self.assertRaises(ValueError):
            self.lm.set_category_discount("meat", "invalid")

    def test_category_discount_is_capped_by_user_max(self):
        self.lm.set_max_discount(30)
        self.lm.set_category_discount("meat", 45)

        result = self.lm.evaluate(
            make_product("Meat"),
            make_ai(percent=10),
            TODAY
    )

        self.assertEqual(result["discount_percent"], 30)

    def test_can_exceed_old_default_if_max_raised(self):
        self.lm.set_max_discount(80)
        self.lm.set_category_discount("meat", 70)
        self.assertEqual(self.lm.get_category_discounts()["meat"], 70)

    def test_remove_category_discount(self):
        self.lm.set_category_discount("meat", 40)
        self.lm.remove_category_discount("meat")
        self.assertNotIn("meat", self.lm.get_category_discounts())

    def test_remove_others_resets_to_default(self):
        self.lm.set_category_discount("meet", 35)
        self.lm.remove_category_discount("others")
        self.assertEqual(self.lm.get_category_discounts()[OTHERS_CATEGORY], DEFAULT_OTHERS_DISCOUNT)


class TestGetFinalDiscount(unittest.TestCase):
    def setUp(self):
        self.lm = new_manager()

    def test_category_discount_overrides_ai(self):
        self.lm.set_category_discount("meat", 40)
        self.assertEqual(self.lm.get_final_discount(make_product("Meat"), 15), 40)

    def test_no_category_discount_keeps_ai(self):
        self.assertEqual(self.lm.get_final_discount(make_product("Berries"), 15), 15)

    def test_unknown_category_uses_others_discount(self):
        self.assertEqual(self.lm.get_final_discount(make_product("Hardware"), 15), DEFAULT_OTHERS_DISCOUNT)

    def test_plural_product_category_still_matches(self):
        self.lm.set_category_discount("meat", 40)
        self.assertEqual(self.lm.get_final_discount(make_product("meats"), 15), 40)


class TestEvaluateRules(unittest.TestCase):
    def setUp(self):
        self.lm = new_manager()

    def test_r1_expired(self):
        result = self.lm.evaluate(make_product(days_left=-1), make_ai(), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_EXPIRED)
        self.assertEqual(result["discount_percent"], 0)
        self.assertFalse(result["needs_staff_approval"])

    def test_r2_not_near_expiry(self):
        result = self.lm.evaluate(make_product(days_left=8), make_ai(), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_NOT_NEAR_EXPIRY)
        self.assertEqual(result["discount_percent"], 0)

    def test_r2_boundary_7_days_is_near_expiry(self):
        result = self.lm.evaluate(make_product("Berries", days_left=7), make_ai(), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_DISCOUNT)

    def test_r1_boundary_expires_today_is_not_expired(self):
        result = self.lm.evaluate(make_product(days_left=0), make_ai(), TODAY)
        self.assertNotEqual(result["outcome"], OUTCOME_EXPIRED)

    def test_r3_ai_failed(self):
        result = self.lm.evaluate(make_product(), make_ai(status="error"), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_MANUAL_REVIEW)
        self.assertEqual(result["discount_percent"], 0)

    def test_r4_urgent_uses_min_discount(self):
        # Berries has no category discount, AI says 10, urgent minimum is 30
        result = self.lm.evaluate(
            make_product("Berries", days_left=2),
            make_ai(risk="high", percent=10, unsold=6), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_URGENT_DISCOUNT)
        self.assertEqual(result["discount_percent"], 30)

    def test_r4_not_urgent_if_unsold_ratio_low(self):
        result = self.lm.evaluate(
            make_product("Berries", days_left=2),
            make_ai(risk="high", percent=10, unsold=4), TODAY)    # 4/10 < 0.5
        self.assertEqual(result["outcome"], OUTCOME_DISCOUNT)

    def test_r4_not_urgent_if_more_than_3_days(self):
        result = self.lm.evaluate(
            make_product("Berries", days_left=4),
            make_ai(risk="high", percent=10, unsold=6), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_DISCOUNT)

    def test_r5_normal_discount_uses_ai(self):
        result = self.lm.evaluate(make_product("Berries"), make_ai(percent=15), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_DISCOUNT)
        self.assertEqual(result["discount_percent"], 15)
        self.assertTrue(result["needs_staff_approval"])

    def test_r6_low_risk_monitor(self):
        result = self.lm.evaluate(make_product("Berries"), make_ai(risk="low", percent=15), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_MONITOR)
        self.assertEqual(result["discount_percent"], 0)

    def test_r6_ai_suggests_zero(self):
        result = self.lm.evaluate(make_product("Berries"), make_ai(risk="medium", percent=0), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_MONITOR)


class TestEvaluateWithUserSettings(unittest.TestCase):
    def setUp(self):
        self.lm = new_manager()

    def test_ai_discount_above_max_is_capped(self):
        self.lm.set_max_discount(30)
        result = self.lm.evaluate(make_product("Berries"), make_ai(percent=45), TODAY)
        self.assertEqual(result["discount_percent"], 30)

    def test_user_max_above_old_default_allows_bigger_discount(self):
        self.lm.set_max_discount(70)
        result = self.lm.evaluate(make_product("Berries"), make_ai(percent=65), TODAY)
        self.assertEqual(result["discount_percent"], 65)

    def test_category_discount_overrides_ai_in_r5(self):
        self.lm.set_category_discount("meat", 40)
        result = self.lm.evaluate(make_product("Meat"), make_ai(percent=15), TODAY)
        self.assertEqual(result["discount_percent"], 40)

    def test_category_discount_can_be_lower_than_ai(self):
        self.lm.set_category_discount("meat", 5)
        result = self.lm.evaluate(make_product("Meat"), make_ai(percent=30), TODAY)
        self.assertEqual(result["discount_percent"], 5)

    def test_category_discount_overrides_in_urgent_rule(self):
        self.lm.set_category_discount("meat", 45)
        result = self.lm.evaluate(
            make_product("Meat", days_left=1),
            make_ai(risk="high", percent=10, unsold=8), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_URGENT_DISCOUNT)
        self.assertEqual(result["discount_percent"], 45)

    def test_lowering_max_caps_existing_category_discount(self):
        self.lm.set_category_discount("meat", 45)
        self.lm.set_max_discount(25)
        result = self.lm.evaluate(make_product("Meat"), make_ai(percent=15), TODAY)
        self.assertEqual(result["discount_percent"], 25)

    def test_unknown_category_gets_others_discount(self):
        result = self.lm.evaluate(make_product("Hardware"), make_ai(percent=15), TODAY)
        self.assertEqual(result["discount_percent"], DEFAULT_OTHERS_DISCOUNT)

    def test_category_discount_not_applied_when_not_near_expiry(self):
        self.lm.set_category_discount("meat", 40)
        result = self.lm.evaluate(make_product("Meat", days_left=10), make_ai(), TODAY)
        self.assertEqual(result["discount_percent"], 0)

    def test_category_discount_not_applied_when_expired(self):
        self.lm.set_category_discount("meat", 40)
        result = self.lm.evaluate(make_product("Meat", days_left=-2), make_ai(), TODAY)
        self.assertEqual(result["discount_percent"], 0)

    def test_category_discount_not_applied_when_ai_failed(self):
        self.lm.set_category_discount("meat", 40)
        result = self.lm.evaluate(make_product("Meat"), make_ai(status="error"), TODAY)
        self.assertEqual(result["outcome"], OUTCOME_MANUAL_REVIEW)
        self.assertEqual(result["discount_percent"], 0)

    def test_category_discount_not_applied_when_low_risk(self):
        self.lm.set_category_discount("meat", 40)

        result = self.lm.evaluate(
            make_product("Meat"),
            make_ai(risk="low"),
            TODAY
        )

        self.assertEqual(result["discount_percent"], 40)
        self.assertEqual(result["outcome"], OUTCOME_DISCOUNT)

    def test_final_price_uses_final_discount(self):
        self.lm.set_category_discount("meat", 40)
        result = self.lm.evaluate(make_product("Meat", price=10.0), make_ai(percent=15), TODAY)
        self.assertEqual(result["final_price"], 6.0)


class TestCalculations(unittest.TestCase):
    def setUp(self):
        self.lm = new_manager()

    def test_days_until_expiry(self):
        self.assertEqual(self.lm.days_until_expiry("2026-11-20", TODAY), 3)
        self.assertEqual(self.lm.days_until_expiry("2026-11-17", TODAY), 0)
        self.assertEqual(self.lm.days_until_expiry("2026-11-15", TODAY), -2)

    def test_apply_discount_cap(self):
        self.assertEqual(self.lm.apply_discount_cap(60, 50), 50)
        self.assertEqual(self.lm.apply_discount_cap(-5, 50), 0)
        self.assertEqual(self.lm.apply_discount_cap(20, 50), 20)

    def test_calculate_final_price(self):
        self.assertEqual(self.lm.calculate_final_price(10.0, 25), 7.5)
        self.assertEqual(self.lm.calculate_final_price(10.0, 0), 10.0)

    def test_unsold_ratio_zero_quantity(self):
        self.assertEqual(self.lm.calculate_unsold_ratio(5, 0), 0)

    def test_waste_cost(self):
        self.assertEqual(self.lm.calculate_waste_cost(3, 4.5), 13.5)


class TestSettingsSaveLoad(unittest.TestCase):
    def setUp(self):
        self.manager = new_manager()
        self.product = make_product("Fruits")
        self.ai_result = make_ai()
        self.today = TODAY

    def test_round_trip(self):
        lm = new_manager()
        lm.set_max_discount(60)
        lm.set_category_discount("meat", 55)
        lm.set_category_discount("meet", 25)
        settings = lm.get_settings()

        lm2 = new_manager()
        lm2.load_settings(settings)
        self.assertEqual(lm2.get_settings(), settings)

    def test_load_empty_settings_keeps_defaults(self):
        lm = new_manager()
        lm.load_settings({})
        self.assertEqual(lm.get_max_discount(), MAX_DISCOUNT_PERCENT)

    def test_get_settings_is_a_copy(self):
        lm = new_manager()
        settings = lm.get_settings()
        settings["category_discounts"]["meat"] = 99
        self.assertNotIn("meat", lm.get_category_discounts())


    def test_load_categories(self):
        products = [
            {"category": "fruits"},
            {"category": "vegetables"},
            {"category": "dairy"}
        ]

        self.manager.load_categories(products)

        self.assertEqual(
            self.manager.get_known_categories(),
            ["dairy", "fruit", "vegetable"]
        )


    def test_unknown_category_goes_to_others(self):
        self.manager.load_categories([
            {"category": "fruits"},
            {"category": "dairy"}
        ])

        result = self.manager.resolve_category("ducks")

        self.assertEqual(result, "others")


    def test_empty_category_goes_to_others(self):
        self.manager.load_categories([
            {"category": "fruits"}
        ])

        self.assertEqual(
            self.manager.resolve_category(""),
            "others"
        )


    def test_unknown_category_discount(self):
        self.manager.load_categories([
            {"category": "fruits"}
        ])

        bucket = self.manager.set_category_discount("ducks", 30)

        self.assertEqual(bucket, "others")
        self.assertEqual(
            self.manager.get_category_discounts()["others"], 30
        )


    def test_category_case_normalization(self):
        self.manager.load_categories([
            {"category": "fruits"}
        ])

        self.assertEqual(
            self.manager.resolve_category("FRUITS"),
            "fruit"
        )


    def test_category_overrides_zero_ai(self):
        self.manager.set_category_discount("fruits", 25)

        self.ai_result["risk_level"] = "low"
        self.ai_result["recommended_discount_percent"] = 0

        result = self.manager.evaluate(
            self.product, self.ai_result, self.today
        )

        self.assertEqual(result["discount_percent"], 25)


    def test_category_overrides_high_ai(self):
        self.manager.set_category_discount("fruits", 20)

        self.ai_result["risk_level"] = "high"
        self.ai_result["recommended_discount_percent"] = 60

        result = self.manager.evaluate(
            self.product, self.ai_result, self.today
        )

        self.assertEqual(result["discount_percent"], 20)


    def test_category_discount_respects_maximum(self):
        self.manager.set_max_discount(30)
        self.manager.set_category_discount("fruits", 50)

        result = self.manager.evaluate(
            self.product, self.ai_result, self.today
        )

        self.assertEqual(result["discount_percent"], 30)


    def test_zero_category_discount_blocks_ai(self):
        self.manager.set_category_discount("fruits", 0)

        self.ai_result["risk_level"] = "high"
        self.ai_result["recommended_discount_percent"] = 50

        result = self.manager.evaluate(
            self.product, self.ai_result, self.today
        )

        self.assertEqual(result["discount_percent"], 0)


    def test_expired_product_ignores_category_discount(self):
        self.manager.set_category_discount("fruits", 30)

        product = self.product.copy()
        product["expiry_date"] = "2026-11-16"

        result = self.manager.evaluate(
            product, self.ai_result, self.today
        )

        self.assertEqual(result["discount_percent"], 0)
        self.assertEqual(result["outcome"], OUTCOME_EXPIRED)


if __name__ == "__main__":
    unittest.main()
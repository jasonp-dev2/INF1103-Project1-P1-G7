import unittest
from datetime import date
from logicManagerClass import logicManager, OUTCOME_DISCOUNT, OUTCOME_URGENT_DISCOUNT

class TestLogicManagerCategoryDiscount(unittest.TestCase):

    def setUp(self):
        self.manager = logicManager()
        self.today = date(2026, 6, 1)

    def test_category_discount_overrides_ai_discount(self):
        # Arrange: Set category 'bakery' to 50% discount
        self.manager.set_category_discount("bakery", 50.0)

        product = {
            "id": "P1",
            "category": "bakery",
            "expiry_date": "2026-06-03", # 2 days left (near expiry)
            "current_price": 10.0,
            "quantity_in_stock": 20
        }
        
        ai_result = {
            "status": "ok",
            "risk_level": "medium",
            "recommended_discount_percent": 30.0, # AI suggests 30%
            "predicted_unsold_quantity": 5.0,
            "predicted_unsold_ratio": 0.25
        }

        # Act: Evaluate the product
        result = self.manager.evaluate(product, ai_result, self.today)

        # Assert: The final discount should be overridden to 50% by the category rule
        self.assertEqual(result["discount_percent"], 50.0)
        self.assertEqual(result["outcome"], OUTCOME_DISCOUNT)

    def test_no_category_discount_uses_ai_discount(self):
        # Arrange: No category discount set for 'dairy'
        product = {
            "id": "P2",
            "category": "dairy",
            "expiry_date": "2026-06-03",
            "current_price": 10.0,
            "quantity_in_stock": 20
        }
        
        ai_result = {
            "status": "ok",
            "risk_level": "medium",
            "recommended_discount_percent": 30.0, # AI suggests 30%
            "predicted_unsold_quantity": 5.0,
            "predicted_unsold_ratio": 0.25
        }

        # Act
        result = self.manager.evaluate(product, ai_result, self.today)

        # Assert: Should keep the AI recommended 30% discount
        self.assertEqual(result["discount_percent"], 30.0)

    def test_category_discount_capped_at_max(self):
        # Arrange: Set category discount higher than MAX_DISCOUNT_PERCENT (50%)
        # Note: set_category_discount raises ValueError if > 50, so test boundary 50
        self.manager.set_category_discount("beverages", 50.0)

        product = {
            "id": "P3",
            "category": "beverages",
            "expiry_date": "2026-06-01", # Urgent expiry
            "current_price": 20.0,
            "quantity_in_stock": 10
        }
        
        ai_result = {
            "status": "ok",
            "risk_level": "high",
            "recommended_discount_percent": 20.0,
            "predicted_unsold_quantity": 6.0,
            "predicted_unsold_ratio": 0.6
        }

        # Act
        result = self.manager.evaluate(product, ai_result, self.today)

        # Assert: Capped cleanly at 50.0
        self.assertEqual(result["discount_percent"], 50.0)
        self.assertEqual(result["outcome"], OUTCOME_URGENT_DISCOUNT)

if __name__ == "__main__":
    unittest.main()
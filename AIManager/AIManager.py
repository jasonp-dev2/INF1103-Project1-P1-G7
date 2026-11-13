import json
import logging
from datetime import date

from AIManager.GeminiClient import GeminiClient
from AIManager.AIService import AIService

logger = logging.getLogger(__name__)


class AIManager:
    """Manager class handling product assessment, prompts, parsing, and validation using the exact original functions."""

    # Class-level constants / attributes
    STATUS_OK = "ok"
    STATUS_FAILED = "failed"
    RISK_LEVELS = ["low", "medium", "high"]
    REQUIRED_KEYS = [
        "risk_level",
        "recommended_discount_percent",
        "predicted_unsold_quantity",
    ]

    def __init__(self, ai_client: AIService = None):
        # Dependency Injection with Polymorphism
        self.ai_client = ai_client or GeminiClient()

    # ---------------------------------------------------------------------------
    # Write the prompt to AI
    # ---------------------------------------------------------------------------

    def build_prompt(self, product: dict, today: date) -> str:
        expiry = date.fromisoformat(product["expiry_date"])
        days_left = (expiry - today).days

        return f"""You are an inventory analyst for a Singapore supermarket.

Your task is to assess the risk of a food product remaining unsold
before its expiry date.

Use only the information provided.

Product information:
- Product name: {product["product_name"]}
- Category: {product["category"]}
- Quantity in stock: {product["quantity_in_stock"]}
- Expiry date: {product["expiry_date"]}
- Days until expiry: {days_left}
- Current selling price: ${product["current_price"]:.2f}

Consider:
1. How perishable the product category is.
2. How much time remains before expiry.
3. Whether the stock quantity is realistic to sell.

Return only a JSON object with exactly these fields:
{{
  "risk_level": "low" | "medium" | "high",
  "recommended_discount_percent": integer from 0 to 90,
  "predicted_unsold_quantity": integer from 0 to {product["quantity_in_stock"]}
}}

Rules:
- Do not include markdown or explanations outside the JSON.
"""

    # ---------------------------------------------------------------------------
    # Turn the AI's text reply into a dictionary
    # ---------------------------------------------------------------------------

    def parse_response(self, raw_text: str) -> dict:
        if not raw_text:
            return {}

        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Gemini returned invalid JSON.")
            return {}

        if type(data) is not dict:
            return {}

        return data

    # ---------------------------------------------------------------------------
    # Double check whether the dictionary makes sense
    # ---------------------------------------------------------------------------

    def is_number(self, value) -> bool:
        return type(value) in [int, float]

    def is_valid_response(self, data: dict, quantity: int) -> bool:
        for key in self.REQUIRED_KEYS:
            if key not in data:
                return False

        if data["risk_level"] not in self.RISK_LEVELS:
            return False

        discount = data["recommended_discount_percent"]

        if not self.is_number(discount) or not 0 <= discount <= 100:
            return False

        unsold = data["predicted_unsold_quantity"]

        if type(unsold) is not int or not 0 <= unsold <= quantity:
            return False

        return True

    def make_failed_result(self, error: str) -> dict:
        return {
            "status": self.STATUS_FAILED,
            "error": error,
        }

    def check_reply(self, raw_text: str, quantity: int, model_name: str) -> dict:
        data = self.parse_response(raw_text)

        if data == {}:
            return self.make_failed_result("Gemini returned invalid JSON.")

        if not self.is_valid_response(data, quantity):
            return self.make_failed_result("Gemini returned missing or invalid values.")

        # All checks passed, build the final result

        return {
            "status": self.STATUS_OK,
            "risk_level": data["risk_level"],
            "recommended_discount_percent": data["recommended_discount_percent"],
            "predicted_unsold_quantity": data["predicted_unsold_quantity"],
            "model_used": model_name,
        }

    # ---------------------------------------------------------------------------
    # Assess product and return the result
    # ---------------------------------------------------------------------------

    def assess_product(self, product: dict, today: date) -> dict:
        try:
            if not self.ai_client.is_configured():
                return self.make_failed_result("Gemini API key is not configured.")

            prompt = self.build_prompt(product, today)
            raw_text, model_name = self.ai_client.call_api(prompt)

            if raw_text == "":
                return self.make_failed_result("Gemini service could not be reached.")

            return self.check_reply(raw_text, product["quantity_in_stock"], model_name)

        except Exception as error:
            logger.error("Unexpected error in assess_product: %s", error)
            return self.make_failed_result("Unexpected error while assessing product.")
import json
import logging
import os
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

logger = logging.getLogger(__name__)

MODEL_NAMES = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
]

# Temporary errors: worth trying the next model for
RETRYABLE_CODES = {429, 500, 503, 504}

# Model not found / not available to this key: skip straight to next model
SKIP_MODEL_CODES = {404}

STATUS_OK = "ok"
STATUS_FAILED = "failed"

RISK_LEVELS = ["low", "medium", "high"]

REQUIRED_KEYS = [
    "risk_level",
    "recommended_discount_percent",
    "predicted_unsold_quantity",
]

# ---------------------------------------------------------------------------
# Connect to Gemini
# ---------------------------------------------------------------------------

def create_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    return genai.Client(api_key=api_key)


def is_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))

# ---------------------------------------------------------------------------
# Write the prompt to AI
# ---------------------------------------------------------------------------

def build_prompt(product: dict, today: date) -> str:
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
# Send the question and get a reply
# ---------------------------------------------------------------------------

def call_api(prompt: str) -> tuple:
    try:
        client = create_client()
    except ValueError as error:
        logger.error("Gemini client setup failed: %s", error)
        return "", ""

    for model_name in MODEL_NAMES:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            if response.text:
                if model_name != MODEL_NAMES[0]:
                    logger.info("Used fallback model: %s", model_name)
                return response.text.strip(), model_name

            logger.warning("%s returned an empty response.", model_name)

        except errors.APIError as error:
            code = getattr(error, "code", None)

            if code not in SKIP_MODEL_CODES and code not in RETRYABLE_CODES:
                logger.error("Non-retryable Gemini error (%s): %s", code, error)
                return "", ""

            logger.warning("%s failed (%s), trying next model.", model_name, code)

        except Exception as error:
            logger.warning("%s failed: %s", model_name, error)

    logger.error("All Gemini models failed.")     # Every model in the list was tried and none of them worked.
    return "", ""

# ---------------------------------------------------------------------------
# Turn the AI's text reply into a dictionary
# ---------------------------------------------------------------------------

def parse_response(raw_text: str) -> dict:
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

def is_number(value) -> bool:
    return type(value) in [int, float]

def is_valid_response(data: dict, quantity: int) -> bool:
    for key in REQUIRED_KEYS:
        if key not in data:
            return False

    if data["risk_level"] not in RISK_LEVELS:
        return False

    discount = data["recommended_discount_percent"]

    if not is_number(discount) or not 0 <= discount <= 100:
        return False

    unsold = data["predicted_unsold_quantity"]

    if type(unsold) is not int or not 0 <= unsold <= quantity:
        return False

    return True

def make_failed_result(error: str) -> dict:
    return {
        "status": STATUS_FAILED,
        "error": error,
    }

def check_reply(raw_text: str, quantity: int, model_name: str) -> dict:
    data = parse_response(raw_text)

    if data == {}:
        return make_failed_result("Gemini returned invalid JSON.")

    if not is_valid_response(data, quantity):
        return make_failed_result("Gemini returned missing or invalid values.")

    # All checks passed, build the final result

    return {
        "status": STATUS_OK,
        "risk_level": data["risk_level"],
        "recommended_discount_percent": data["recommended_discount_percent"],
        "predicted_unsold_quantity": data["predicted_unsold_quantity"],
        "model_used": model_name,
    }

# ---------------------------------------------------------------------------
# Assess product and return the result
# ---------------------------------------------------------------------------

def assess_product(product: dict, today: date) -> dict:
    try:
        if not is_configured():
            return make_failed_result("Gemini API key is not configured.")

        prompt = build_prompt(product, today)
        raw_text, model_name = call_api(prompt)

        if raw_text == "":
            return make_failed_result("Gemini service could not be reached.")

        return check_reply(raw_text, product["quantity_in_stock"], model_name)

    except Exception as error:
        logger.error("Unexpected error in assess_product: %s", error)
        return make_failed_result("Unexpected error while assessing product.")
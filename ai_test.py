from dotenv import load_dotenv
import os
import json
import time
from google import genai

load_dotenv()

MODEL_NAME = "gemini-3.8-flash"
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite"
]
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


def build_prompt(record):
    """Build the prompt that will be sent to Gemini."""

    return f"""
You are to analyse one supermarket product for expiry and waste risk.

Product:
- Product Name: {record["product_name"]}
- Category: {record["category"]}
- Quantity in stock: {record["quantity"]}
- Current selling price: {record["selling_price"]}

Analyse this product and return ONLY valid JSON using this structure:

{{
  "risk_level": "LOW | MEDIUM | HIGH",
  "predicted_units_unsold": 0,
  "recommended_discount": 0.0,
  "waste_cost_if_unsold": 0.0
}}

Rules:
- risk_level must be exactly LOW, MEDIUM, or HIGH.
- predicted_units_unsold must be an integer from 0 to the quantity in stock.
- recommended_discount must be a number from 0 to 100.
- waste_cost_if_unsold must be a non-negative number.
- Do not include any extra fields.
""".strip()


def analyse_product(record):

    prompt = build_prompt(record)

    for model in MODELS:

        print(f"[INFO] Trying {model}...")

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            print(f"[OK] Response received from {model}")

            return response.text

        except Exception as error:

            print(f"[ERROR] {model} failed:")
            print(error)

            print("[INFO] Trying next model...")

    raise Exception("All Gemini models failed.")


def validate_response(response_text, quantity):
    """Validate the JSON returned by Gemini."""

    try:
        data = json.loads(response_text)

    except json.JSONDecodeError:
        print("[ERROR] Gemini returned invalid JSON.")
        print(response_text)
        return None

    expected_fields = {
        "risk_level",
        "predicted_units_unsold",
        "recommended_discount",
        "waste_cost_if_unsold"
    }

    if set(data.keys()) != expected_fields:
        print("[ERROR] Incorrect fields returned.")
        return None

    if data["risk_level"] not in ["LOW", "MEDIUM", "HIGH"]:
        print("[ERROR] Invalid risk level.")
        return None

    if not isinstance(data["predicted_units_unsold"], int):
        print("[ERROR] predicted_units_unsold must be an integer.")
        return None

    if not 0 <= data["predicted_units_unsold"] <= quantity:
        print("[ERROR] predicted_units_unsold is outside valid range.")
        return None

    if not isinstance(data["recommended_discount"], (int, float)):
        print("[ERROR] recommended_discount must be a number.")
        return None

    if not 0 <= data["recommended_discount"] <= 100:
        print("[ERROR] recommended_discount must be between 0 and 100.")
        return None

    if not isinstance(data["waste_cost_if_unsold"], (int, float)):
        print("[ERROR] waste_cost_if_unsold must be a number.")
        return None

    if data["waste_cost_if_unsold"] < 0:
        print("[ERROR] waste_cost_if_unsold cannot be negative.")
        return None

    return data


def main():

    product = {
        "product_name": "Fresh Milk 1L",
        "category": "Dairy",
        "quantity": 20,
        "selling_price": 3.50
    }

    try:

        raw_response = analyse_product(product)

        print("\n[AI RAW RESPONSE]")
        print(raw_response)

        result = validate_response(
            raw_response,
            product["quantity"]
        )

        if result is None:
            print("\n[ERROR] AI response validation failed.")
            return

        print("\n[OK] AI response is valid!")

        print("\n[FINAL RESULT]")
        print(json.dumps(result, indent=4))

    except Exception as error:

        print("\n[FAILED]")
        print("Could not get a response from Gemini.")
        print(error)


if __name__ == "__main__":
    main()
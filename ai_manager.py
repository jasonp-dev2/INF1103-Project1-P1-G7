from dotenv import load_dotenv
import os
import json
import time
from google import genai

load_dotenv()


MODEL_NAME = "gemini-3.8-flash"
MODELS = [ #This is a list of models that will be tried in order until one returns a valid response.
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite"
]
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def build_prompt(record): #This function will build the prompt that will be sent to the AI model.
    return f"""
You are to analyse one supermarket product for expiry and waste risk.

Product:
- Product Name: {record["product_name"]}
- Category: {record["category"]}
- Quantity in stock: {record["quantity"]}
- Current selling price {record["selling_price"]}

Analyrse this product and return ONLY valid JSON using this structure:
{{
  "risk_level": "LOW | MEDIUM | HIGH",
  "predicted_units_unsold": 0,
  "recommended_discount": 0.0,
  "waste_cost_if_unsold":0.0  
}}
RULES: 
- predicted_units_unsold must be an integer from 0 to the quantity in stock
- recommended_discount must be a number from 0 to 100
- waste_cost_if_unsold must be a non-negative numnber.
- Do not include any other extra fields.  
""".strip()
 

def validate_response(response, quantity): #This function ensures response is valid JSON and contains the expected fields and values.
    """Validate the response from the AI model."""
    try:
        data=json.loads(response)

    except json.JSONDecodeError:
        print("[ERROR] AI model returned invalid JSON.")
        print(response.text)
        return None
    expected_fields = {"risk_level", "predicted_units_unsold", "recommended_discount", "waste_cost_if_unsold"}

    if set(data.keys()) != expected_fields:
        print("[ERROR] Incorrect fields in AI model response.")
        return None
    if data["risk_level"] not in {"LOW", "MEDIUM", "HIGH"}:
        print("[ERROR] Invalid risk_level value.")
        return None
    if not isinstance(data["predicted_units_unsold"], int) or not (0 <= data["predicted_units_unsold"] <= quantity):
        print("[ERROR] Invalid predicted_units_unsold value.")
        return None
    if not isinstance(data["recommended_discount"], (int, float)) or not (0 <= data["recommended_discount"] <= 100):
        print("[ERROR] Invalid recommended_discount value.")
        return None
    if not isinstance(data["waste_cost_if_unsold"], (int, float)) or data["waste_cost_if_unsold"] < 0:
        print("[ERROR] Invalid waste_cost_if_unsold value.")
        return None
    return data

def analyse_product(record): #This function will try each model in the MODELS list until it gets a valid response or all models fail

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

    raise Exception("All models failed.")   


    
def main() -> None: #This is the test function that will be run when the script is executed. It will test the AI connection and then analyse a hardcoded product record.
    product = { #This is hardcoded example of a product record. When part is finished, this will come from user input.
        "product_name": "Fresh Milk 1L",
        "category": "Dairy",
        "quantity": 20,
        "selling_price": 3.50
    }

    try: #This will test the AI connection and then analyse the product record.

        raw_response = analyse_product(product)

        print("\n[AI RESPONSE]")
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
        print("Could not get a response from AI.")
        print(error)


if __name__ == "__main__":
    main()


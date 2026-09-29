from dotenv import load_dotenv
import os
from google import genai

load_dotenv()


MODEL_NAME = "gemini-3.8-flash"
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite"
]
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])




def test_ai_connection() -> str:
    """Test that the Gemini API connection works."""
    client = genai.Client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents="Reply with exactly: AI connection successful",
    )

    return response.text

def build_prompt(record):
    """"This is the prompt that will be sent to AI"""
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
 

def validate_response(response, quantity):
    """Validate the response from the AI model."""
    try:
        data=json.loads(response.text)

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

    


    
def main() -> None:
    """Run a simple Gemini API connection test."""
    try:
        result = test_ai_connection() 
        print("[OK] AI connection successful.")
        print(result)
    except Exception as error:
        print("[ERROR] AI connection failed.")
        print(error)


if __name__ == "__main__":
    main()


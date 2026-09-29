from dotenv import load_dotenv
import os
from google import genai

load_dotenv()


MODEL_NAME = "gemini-3.8-flash"

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
 

def validate_response():

    """This will check if the AI response is correct and reject invalid data"""

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


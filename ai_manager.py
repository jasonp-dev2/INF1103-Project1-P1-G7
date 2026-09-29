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

def build_prompt():
    """"This is the prompt that will be sent to AI"""

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


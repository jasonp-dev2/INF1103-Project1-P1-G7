

from google import genai


MODEL_NAME = "gemini-3.8-flash"


def test_ai_connection() -> str:
    """Test that the Gemini API connection works."""
    client = genai.Client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents="Reply with exactly: AI connection successful",
    )

    return response.text


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


import json
import os
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

from .ai_manager import AIManager
from .gemini_provider import GeminiProvider


class LiveAssessmentDemo:
    """Run one real product assessment through the AI component."""

    def run(self) -> int:
        project_root = Path(__file__).resolve().parents[1]
        load_dotenv(project_root / ".env")

        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        model = os.getenv("GEMINI_MODEL", "").strip()

        if not api_key or not model:
            print("Set GEMINI_API_KEY and GEMINI_MODEL in .env.")
            return 1

        provider = GeminiProvider(
            api_key=api_key,
            model=model,
        )
        manager = AIManager(provider)

        today = date.today()

        product = {
            "product_name": "Fresh milk",
            "category": "Dairy & Eggs",
            "quantity_in_stock": 1500,
            "expiry_date": (today + timedelta(days=8)).isoformat(),
            "current_price": 15.00,
        }

        print(f"Sending one assessment request using {manager.model_name}...")
        result = manager.assess_product(product, today)

        print(json.dumps(result, indent=2))

        if result["status"] != AIManager.STATUS_OK:
            print("Assessment failed. Check the error message above.")
            return 1

        print("AI assessment received and validated.")
        print("The Logic Manager must still apply business rules.")
        return 0


if __name__ == "__main__":
    raise SystemExit(LiveAssessmentDemo().run())
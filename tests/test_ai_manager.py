"""Offline tests for AIManager prompt building, parsing, validation, and failure handling."""
from datetime import date, timedelta

from AIManager.AIManager import AIManager
from AIManager.AIService import AIService

TODAY = date(2026, 11, 18)


class StubAIService(AIService):
    """Test double implementing AIService without live network calls."""

    def __init__(self, configured=True, reply=("", ""), error=None):
        self._configured = configured
        self._reply = reply
        self._error = error
        self.last_prompt = None

    def create_client(self) -> object:
        return object()

    def is_configured(self) -> bool:
        return self._configured

    def call_api(self, prompt: str) -> tuple:
        self.last_prompt = prompt
        if self._error is not None:
            raise self._error
        return self._reply


def sample_product(quantity=10):
    return {
        "product_name": "Fresh Milk",
        "category": "Dairy & Eggs",
        "quantity_in_stock": quantity,
        "expiry_date": (TODAY + timedelta(days=2)).isoformat(),
        "current_price": 4.50,
    }


def test_build_prompt_includes_product_and_json_fields():
    manager = AIManager(ai_client=StubAIService())
    prompt = manager.build_prompt(sample_product(), TODAY)
    assert "Fresh Milk" in prompt
    assert "Dairy & Eggs" in prompt
    assert "Days until expiry: 2" in prompt
    assert "risk_level" in prompt
    assert "recommended_discount_percent" in prompt
    assert "predicted_unsold_quantity" in prompt


def test_parse_response_accepts_plain_and_fenced_json():
    manager = AIManager(ai_client=StubAIService())
    fenced = '```json\n{"risk_level": "high", "recommended_discount_percent": 30, "predicted_unsold_quantity": 5}\n```'
    parsed = manager.parse_response(fenced)
    assert parsed["risk_level"] == "high"
    assert parsed["recommended_discount_percent"] == 30
    assert parsed["predicted_unsold_quantity"] == 5


def test_parse_response_rejects_malformed_or_non_dict_json():
    manager = AIManager(ai_client=StubAIService())
    assert manager.parse_response("") == {}
    assert manager.parse_response("not json at all") == {}
    assert manager.parse_response('["a", "b"]') == {}


def test_is_valid_response_checks_schema_and_bounds():
    manager = AIManager(ai_client=StubAIService())
    valid = {
        "risk_level": "medium",
        "recommended_discount_percent": 25,
        "predicted_unsold_quantity": 4,
    }
    assert manager.is_valid_response(valid, quantity=10) is True
    assert manager.is_valid_response({**valid, "risk_level": "extreme"}, 10) is False
    assert manager.is_valid_response({**valid, "recommended_discount_percent": 105}, 10) is False
    assert manager.is_valid_response({**valid, "recommended_discount_percent": True}, 10) is False
    assert manager.is_valid_response({**valid, "predicted_unsold_quantity": 11}, 10) is False
    assert manager.is_valid_response({**valid, "predicted_unsold_quantity": 2.5}, 10) is False
    assert manager.is_valid_response({"risk_level": "low"}, 10) is False


def test_assess_product_handles_unconfigured_and_unreachable_client():
    unconfigured = AIManager(ai_client=StubAIService(configured=False))
    result = unconfigured.assess_product(sample_product(), TODAY)
    assert result["status"] == AIManager.STATUS_FAILED

    unreachable = AIManager(ai_client=StubAIService(configured=True, reply=("", "")))
    result = unreachable.assess_product(sample_product(), TODAY)
    assert result["status"] == AIManager.STATUS_FAILED


def test_assess_product_handles_malformed_output_and_client_exception():
    malformed = AIManager(ai_client=StubAIService(reply=("{bad json", "gemini-stub")))
    assert malformed.assess_product(sample_product(), TODAY)["status"] == AIManager.STATUS_FAILED

    invalid_schema = AIManager(
        ai_client=StubAIService(
            reply=('{"risk_level": "high", "recommended_discount_percent": 20, "predicted_unsold_quantity": 99}', "gemini-stub")
        )
    )
    assert invalid_schema.assess_product(sample_product(quantity=5), TODAY)["status"] == AIManager.STATUS_FAILED

    crashing = AIManager(ai_client=StubAIService(error=RuntimeError("timeout")))
    assert crashing.assess_product(sample_product(), TODAY)["status"] == AIManager.STATUS_FAILED


def test_assess_product_returns_validated_result():
    stub = StubAIService(
        reply=('{"risk_level": "high", "recommended_discount_percent": 35, "predicted_unsold_quantity": 6}', "gemini-stub")
    )
    manager = AIManager(ai_client=stub)
    result = manager.assess_product(sample_product(quantity=10), TODAY)
    assert result["status"] == AIManager.STATUS_OK
    assert result["risk_level"] == "high"
    assert result["recommended_discount_percent"] == 35
    assert result["predicted_unsold_quantity"] == 6
    assert result["model_used"] == "gemini-stub"

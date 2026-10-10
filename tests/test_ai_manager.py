"""
Tests for ai_manager.py.
"""
import json
from datetime import date

import ai_manager

TODAY = date(2026, 10, 10)

PRODUCT = {
    "product_name": "Milk",
    "category": "Dairy & Eggs",
    "quantity_in_stock": 10,
    "expiry_date": "2026-10-13",
    "current_price": 4.50,
}

GOOD_REPLY = {
    "risk_level": "high",
    "recommended_discount_percent": 30,
    "predicted_unsold_quantity": 6,
}


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------

def test_build_prompt_contains_product_details_and_days_left():
    prompt = ai_manager.build_prompt(PRODUCT, TODAY)
    assert "Milk" in prompt
    assert "Dairy & Eggs" in prompt
    assert "Days until expiry: 3" in prompt
    assert "$4.50" in prompt


# ---------------------------------------------------------------------------
# parse_response: turns the AI's text into a dictionary
# ---------------------------------------------------------------------------

def test_parse_response_plain_json():
    assert ai_manager.parse_response(json.dumps(GOOD_REPLY)) == GOOD_REPLY


def test_parse_response_json_inside_markdown_fence():
    text = "```json\n" + json.dumps(GOOD_REPLY) + "\n```"
    assert ai_manager.parse_response(text) == GOOD_REPLY


def test_parse_response_empty_text_gives_empty_dict():
    assert ai_manager.parse_response("") == {}


def test_parse_response_invalid_json_gives_empty_dict():
    assert ai_manager.parse_response("Sorry, I cannot help with that.") == {}


def test_parse_response_json_list_gives_empty_dict():
    assert ai_manager.parse_response("[1, 2, 3]") == {}


# ---------------------------------------------------------------------------
# is_valid_response: checks the dictionary makes sense
# ---------------------------------------------------------------------------

def test_valid_response_accepted():
    assert ai_manager.is_valid_response(GOOD_REPLY, 10) is True


def test_missing_key_rejected():
    data = dict(GOOD_REPLY)
    del data["risk_level"]
    assert ai_manager.is_valid_response(data, 10) is False


def test_unknown_risk_level_rejected():
    data = dict(GOOD_REPLY, risk_level="extreme")
    assert ai_manager.is_valid_response(data, 10) is False


def test_discount_out_of_range_rejected():
    assert ai_manager.is_valid_response(dict(GOOD_REPLY, recommended_discount_percent=150), 10) is False
    assert ai_manager.is_valid_response(dict(GOOD_REPLY, recommended_discount_percent=-5), 10) is False


def test_discount_as_text_rejected():
    data = dict(GOOD_REPLY, recommended_discount_percent="30")
    assert ai_manager.is_valid_response(data, 10) is False


def test_unsold_more_than_stock_rejected():
    data = dict(GOOD_REPLY, predicted_unsold_quantity=11)
    assert ai_manager.is_valid_response(data, 10) is False


def test_unsold_decimal_rejected():
    data = dict(GOOD_REPLY, predicted_unsold_quantity=2.5)
    assert ai_manager.is_valid_response(data, 10) is False


# ---------------------------------------------------------------------------
# check_reply: parse + validate together
# ---------------------------------------------------------------------------

def test_check_reply_success():
    result = ai_manager.check_reply(json.dumps(GOOD_REPLY), 10, "gemini-test")
    assert result["status"] == "ok"
    assert result["risk_level"] == "high"
    assert result["model_used"] == "gemini-test"


def test_check_reply_invalid_json_fails():
    result = ai_manager.check_reply("not json", 10, "gemini-test")
    assert result["status"] == "failed"
    assert "invalid JSON" in result["error"]


def test_check_reply_bad_values_fails():
    bad = dict(GOOD_REPLY, risk_level="extreme")
    result = ai_manager.check_reply(json.dumps(bad), 10, "gemini-test")
    assert result["status"] == "failed"
    assert "missing or invalid" in result["error"]


# ---------------------------------------------------------------------------
# call_api: model fallback and failure (fake Gemini client)
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, plan):
        self.plan = list(plan)
        self.calls = 0

    def generate_content(self, model, contents):
        action = self.plan[self.calls]
        self.calls += 1
        if isinstance(action, Exception):
            raise action
        return FakeResponse(action)


class FakeClient:
    def __init__(self, plan):
        self.models = FakeModels(plan)


def test_call_api_returns_reply_from_first_model(monkeypatch):
    client = FakeClient(['{"ok": true}'])
    monkeypatch.setattr(ai_manager, "create_client", lambda: client)
    text, model = ai_manager.call_api("prompt")
    assert text == '{"ok": true}'
    assert model == ai_manager.MODEL_NAMES[0]


def test_call_api_falls_back_to_second_model(monkeypatch):
    client = FakeClient([Exception("model down"), '{"ok": true}'])
    monkeypatch.setattr(ai_manager, "create_client", lambda: client)
    text, model = ai_manager.call_api("prompt")
    assert text == '{"ok": true}'
    assert model == ai_manager.MODEL_NAMES[1]


def test_call_api_all_models_fail_returns_empty(monkeypatch):
    client = FakeClient([Exception("down"), Exception("down")])
    monkeypatch.setattr(ai_manager, "create_client", lambda: client)
    assert ai_manager.call_api("prompt") == ("", "")


def test_call_api_missing_key_returns_empty(monkeypatch):
    def no_key():
        raise ValueError("GEMINI_API_KEY is missing from .env")
    monkeypatch.setattr(ai_manager, "create_client", no_key)
    assert ai_manager.call_api("prompt") == ("", "")


# ---------------------------------------------------------------------------
# assess_product: the full AI step, never crashes
# ---------------------------------------------------------------------------

def test_assess_product_success(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(ai_manager, "call_api",
                        lambda prompt: (json.dumps(GOOD_REPLY), "gemini-test"))
    result = ai_manager.assess_product(PRODUCT, TODAY)
    assert result["status"] == "ok"
    assert result["predicted_unsold_quantity"] == 6


def test_assess_product_without_api_key_fails_gracefully(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = ai_manager.assess_product(PRODUCT, TODAY)
    assert result["status"] == "failed"
    assert "not configured" in result["error"]


def test_assess_product_service_unreachable(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(ai_manager, "call_api", lambda prompt: ("", ""))
    result = ai_manager.assess_product(PRODUCT, TODAY)
    assert result["status"] == "failed"
    assert "could not be reached" in result["error"]


def test_assess_product_malformed_reply(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(ai_manager, "call_api",
                        lambda prompt: ("I think you should discount it", "gemini-test"))
    result = ai_manager.assess_product(PRODUCT, TODAY)
    assert result["status"] == "failed"


def test_assess_product_unexpected_error_does_not_crash(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    def explode(prompt):
        raise RuntimeError("something unexpected")
    monkeypatch.setattr(ai_manager, "call_api", explode)
    result = ai_manager.assess_product(PRODUCT, TODAY)
    assert result["status"] == "failed"
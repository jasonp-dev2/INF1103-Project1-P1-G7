import pytest
import json

from datetime import date
from ai_oop.ai_manager import AIManager
from ai_oop.ai_provider import AIProvider
from ai_oop.ai_provider_error import AIProviderError

class OfflineProvider(AIProvider):
    """A test provider that must not make any AI request."""

    def __init__(self, name: str):
        self._name = name

    @property
    def model_name(self) -> str:
        return self._name

    def generate(self, prompt: str) -> str:
        raise AssertionError(
            "Creating a manager or reading its model name "
            "must not generate an AI response."
        )


@pytest.mark.parametrize(
    "name",
    ["offline-test", "another-model"],
)
def test_manager_reads_provider_name_without_generating(name):
    provider = OfflineProvider(name)
    manager = AIManager(provider)

    assert manager.model_name == name


@pytest.fixture
def product():
    return {
        "product_name": 'Milk "Fresh"',
        "category": "Dairy & Eggs",
        "quantity_in_stock": 10,
        "expiry_date": "2026-11-16",
        "current_price": 5.00,
    }


def test_build_prompt_contains_product_data_without_changing_input(product):
    manager = AIManager(OfflineProvider("offline-test"))
    original = product.copy()

    prompt = manager.build_prompt(product, date(2026, 11, 14))

    # Extract the JSON section to check the actual product information.
    json_text = prompt.split("Product data:\n", 1)[1]
    details = json.loads(json_text)

    assert details == {
        **original,
        "days_until_expiry": 2,
    }
    assert product == original

    # Check that we request all three AI output fields.
    assert "risk_level" in prompt
    assert "recommended_discount_percent" in prompt
    assert "predicted_unsold_quantity" in prompt

    print(prompt)


@pytest.mark.parametrize("quantity", [-1, True, 1.5])
def test_build_prompt_rejects_invalid_stock(product, quantity):
    manager = AIManager(OfflineProvider("offline-test"))
    product["quantity_in_stock"] = quantity

    with pytest.raises(ValueError, match="Stock"):
        manager.build_prompt(product, date(2026, 11, 14))


@pytest.mark.parametrize("price", [0, float("inf"), float("nan")])
def test_build_prompt_rejects_invalid_price(product, price):
    manager = AIManager(OfflineProvider("offline-test"))
    product["current_price"] = price

    with pytest.raises(ValueError, match="Price"):
        manager.build_prompt(product, date(2026, 11, 14))




def test_parse_response_converts_json_into_dictionary():
    manager = AIManager(OfflineProvider("offline-test"))

    raw_text = """
    {
        "risk_level": "high",
        "recommended_discount_percent": 40,
        "predicted_unsold_quantity": 8
    }
    """

    result = manager.parse_response(raw_text)

    assert result == {
        "risk_level": "high",
        "recommended_discount_percent": 40,
        "predicted_unsold_quantity": 8,
    }
    assert isinstance(result["recommended_discount_percent"], int)


@pytest.mark.parametrize(
    "raw_text",
    [
        "",
        "   ",
        "This product looks risky.",
        '{"risk_level": "high",}',
        '```json\n{"risk_level": "high"}\n```',
    ],
)
def test_parse_response_rejects_empty_or_malformed_json(raw_text):
    manager = AIManager(OfflineProvider("offline-test"))

    with pytest.raises(ValueError, match="AI returned"):
        manager.parse_response(raw_text)


@pytest.mark.parametrize(
    "raw_text",
    [
        "[]",
        "null",
        "42",
        '"hello"',
    ],
)
def test_parse_response_rejects_json_that_is_not_an_object(raw_text):
    manager = AIManager(OfflineProvider("offline-test"))

    with pytest.raises(ValueError, match="JSON object"):
        manager.parse_response(raw_text)


@pytest.mark.parametrize(
    "risk, discount, unsold, quantity",
    [
        ("low", 0, 0, 0),
        ("medium", 20.5, 3, 10),
        ("high", 100, 10, 10),
    ],
)
def test_parse_and_validate_accept_valid_assessments(
    risk, discount, unsold, quantity
):
    manager = AIManager(OfflineProvider("offline-test"))

    expected = {
        "risk_level": risk,
        "recommended_discount_percent": discount,
        "predicted_unsold_quantity": unsold,
    }

    # Simulate response text arriving from a provider.
    raw_text = json.dumps(expected)

    data = manager.parse_response(raw_text)
    manager.validate_response(data, quantity)

    # Validation checks the assessment without changing its values.
    assert data == expected


@pytest.fixture
def valid_assessment():
    return {
        "risk_level": "high",
        "recommended_discount_percent": 40,
        "predicted_unsold_quantity": 8,
    }


def test_validate_response_rejects_missing_field(valid_assessment):
    manager = AIManager(OfflineProvider("offline-test"))
    del valid_assessment["risk_level"]

    with pytest.raises(ValueError, match="missing or unexpected"):
        manager.validate_response(valid_assessment, quantity=10)


def test_validate_response_rejects_extra_field(valid_assessment):
    manager = AIManager(OfflineProvider("offline-test"))
    valid_assessment["extra_advice"] = "Sell everything"

    with pytest.raises(ValueError, match="missing or unexpected"):
        manager.validate_response(valid_assessment, quantity=10)



@pytest.mark.parametrize(
    "field, value",
    [
        ("risk_level", "extreme"),
        ("recommended_discount_percent", True),
        ("recommended_discount_percent", "20"),
        ("recommended_discount_percent", -1),
        ("recommended_discount_percent", 101),
        ("recommended_discount_percent", float("nan")),
        ("recommended_discount_percent", float("inf")),
        ("predicted_unsold_quantity", True),
        ("predicted_unsold_quantity", 1.5),
        ("predicted_unsold_quantity", -1),
        ("predicted_unsold_quantity", 11),
        ("predicted_unsold_quantity", "5"),
    ],
)
def test_validate_response_rejects_invalid_values(
    valid_assessment, field, value
):
    manager = AIManager(OfflineProvider("offline-test"))
    valid_assessment[field] = value

    with pytest.raises(ValueError):
        manager.validate_response(valid_assessment, quantity=10)


class StubProvider(AIProvider):
    """Returns a chosen response or simulates a provider failure."""

    def __init__(self, response: str = "", error: str | None = None):
        self._response = response
        self._error = error
        self.prompts: list[str] = []

    @property
    def model_name(self) -> str:
        return "test-model"

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)

        if self._error is not None:
            raise AIProviderError(self._error)

        return self._response

def test_assess_product_runs_the_complete_pipeline(
    product, valid_assessment
):
    provider = StubProvider(
        response=json.dumps(valid_assessment)
    )
    manager = AIManager(provider)

    result = manager.assess_product(product, date(2026, 11, 14))

    assert result == {
        "status": "ok",
        **valid_assessment,
        "model_used": "test-model",
    }

    # Confirm that the manager actually called the provider once.
    assert len(provider.prompts) == 1

    # Confirm that the provider received this product's information.
    prompt_data = json.loads(
        provider.prompts[0].split("Product data:\n", 1)[1]
    )
    assert prompt_data["product_name"] == product["product_name"]
    assert prompt_data["days_until_expiry"] == 2


def test_assess_product_handles_provider_failure(product):
    provider = StubProvider(error="Service unavailable")
    manager = AIManager(provider)

    result = manager.assess_product(product, date(2026, 11, 14))

    assert result == {
        "status": "failed",
        "error": "Service unavailable",
    }
    assert len(provider.prompts) == 1


@pytest.mark.parametrize(
    "response",
    [
        "not JSON",
        "{}",
        json.dumps({
            "risk_level": "high",
            "recommended_discount_percent": 40,
            "predicted_unsold_quantity": 11,
        }),
    ],
)
def test_assess_product_handles_invalid_response(product, response):
    manager = AIManager(StubProvider(response=response))

    result = manager.assess_product(product, date(2026, 11, 14))

    assert result["status"] == "failed"
    assert result["error"]
    assert set(result) == {"status", "error"}


def test_invalid_product_does_not_call_provider(product):
    provider = StubProvider()
    manager = AIManager(provider)
    product["quantity_in_stock"] = -1

    result = manager.assess_product(product, date(2026, 11, 14))

    assert result["status"] == "failed"
    assert provider.prompts == []


def test_missing_product_field_does_not_call_provider(product):
    provider = StubProvider()
    manager = AIManager(provider)
    del product["expiry_date"]

    result = manager.assess_product(product, date(2026, 11, 14))

    assert result["status"] == "failed"
    assert provider.prompts == []
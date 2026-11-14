import pytest
import json

from datetime import date
from ai_oop.ai_manager import AIManager
from ai_oop.ai_provider import AIProvider


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
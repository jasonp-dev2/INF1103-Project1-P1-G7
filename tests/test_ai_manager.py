import pytest

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
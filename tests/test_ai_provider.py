import pytest

from ai_oop.ai_provider import AIProvider
from ai_oop.ai_provider_error import AIProviderError


def test_provider_error_can_be_caught():
    with pytest.raises(AIProviderError, match="Service unavailable"):
        raise AIProviderError("Service unavailable")


def test_abstract_provider_cannot_be_created():
    # AIProvider is only a contract, not a complete implementation.
    with pytest.raises(TypeError):
        AIProvider()


def test_incomplete_provider_cannot_be_created():
    class IncompleteProvider(AIProvider):
        @property
        def model_name(self) -> str:
            return "incomplete"

        # generate() has deliberately not been implemented.

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_complete_provider_can_be_used():
    class OfflineProvider(AIProvider):
        """Used only by this test; does not contact an API."""

        @property
        def model_name(self) -> str:
            return "offline-test"

        def generate(self, prompt: str) -> str:
            return f"Received: {prompt}"

    provider = OfflineProvider()

    assert isinstance(provider, AIProvider)
    assert provider.model_name == "offline-test"
    assert provider.generate("Assess milk") == "Received: Assess milk"
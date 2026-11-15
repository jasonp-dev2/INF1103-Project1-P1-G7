from unittest.mock import MagicMock

import pytest
from google.genai import errors

from ai_oop.ai_provider_error import AIProviderError
from ai_oop.gemini_provider import GeminiProvider


@pytest.fixture
def mocked_sdk(monkeypatch):
    factory = MagicMock()

    # This is the client returned by:
    # with genai.Client(...) as client:
    client = factory.return_value.__enter__.return_value

    monkeypatch.setattr(
        "ai_oop.gemini_provider.genai.Client",
        factory,
    )

    return factory, client


def test_generate_sends_prompt_and_returns_text(mocked_sdk):
    factory, client = mocked_sdk
    client.models.generate_content.return_value.text = ' {"example": 1} '

    provider = GeminiProvider("test-key", "test-model")

    result = provider.generate("Assess this product")

    assert result == '{"example": 1}'
    assert provider.model_name == "test-model"

    arguments = client.models.generate_content.call_args.kwargs
    assert arguments["model"] == "test-model"
    assert arguments["contents"] == "Assess this product"
    assert arguments["config"].response_mime_type == "application/json"

    options = factory.call_args.kwargs["http_options"]
    assert options.timeout == 30000

    # The context manager must close after use.
    factory.return_value.__exit__.assert_called_once()


def test_missing_key_does_not_create_client(mocked_sdk):
    factory, _ = mocked_sdk
    provider = GeminiProvider("", "test-model")

    with pytest.raises(AIProviderError, match="Configure"):
        provider.generate("Assess this product")

    factory.assert_not_called()


def test_timeout_becomes_provider_error(mocked_sdk):
    _, client = mocked_sdk
    client.models.generate_content.side_effect = TimeoutError()

    provider = GeminiProvider("test-key", "test-model")

    with pytest.raises(AIProviderError, match="timed out"):
        provider.generate("Assess this product")


def test_api_failure_becomes_provider_error(mocked_sdk):
    _, client = mocked_sdk
    client.models.generate_content.side_effect = errors.APIError(
        503,
        {"message": "Service unavailable"},
    )

    provider = GeminiProvider("test-key", "test-model")

    with pytest.raises(AIProviderError, match="code 503"):
        provider.generate("Assess this product")


def test_empty_response_becomes_provider_error(mocked_sdk):
    _, client = mocked_sdk
    client.models.generate_content.return_value.text = ""

    provider = GeminiProvider("test-key", "test-model")

    with pytest.raises(AIProviderError, match="no usable response"):
        provider.generate("Assess this product")
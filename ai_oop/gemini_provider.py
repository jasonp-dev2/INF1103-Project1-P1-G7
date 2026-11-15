import httpx
from google import genai
from google.genai import errors, types

from .ai_provider import AIProvider
from .ai_provider_error import AIProviderError

class GeminiProvider(AIProvider):

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key.strip()
        self._model = model.strip()


    @property
    def model_name(self) -> str:
        return self._model
    
    def generate(self, prompt: str) -> str:
        if not self._api_key or not self._model:
            raise AIProviderError("Configure a Gemini API key and model first.")

        try:
            with genai.Client(
                api_key=self._api_key,
                http_options=types.HttpOptions(
                    timeout=30000,
                    retry_options=types.HttpRetryOptions(
                        attempts=3,
                        initial_delay=1,
                        max_delay=4,
                        http_status_codes=[500,503,504],
                        ),
                ),
            ) as client:
                response = client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        automatic_function_calling=(
                            types.AutomaticFunctionCallingConfig(
                                disable=True,
                            )
                        )
                    ),
                )


                raw_text = response.text

        except errors.APIError as error:
            raise AIProviderError(
                f"Gemini request failed (code {error.code})."
                "Check configuration or retry later."
            ) from error

        except (httpx.TimeoutException, TimeoutError) as error:
            raise AIProviderError(
                "Gemini request timed out. Retry later"
                ) from error
        except (httpx.RequestError, OSError) as error:
            raise AIProviderError(
                "Could not connect to Gemini. Retry later."
            ) from error

        except ValueError as error:
            raise AIProviderError(
                "Gemini configuration or response was invalid."
            ) from error

        if not isinstance(raw_text, str) or not raw_text.strip():
            raise AIProviderError(
                "Gemini returned no usable response text."
            )

        return raw_text.strip()
        
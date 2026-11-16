import json
import logging
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from google import genai
from google.genai import errors

from AIManager.AIService import AIService

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiClient(AIService):
    """Gemini API client implementing AIService interface."""

    MODEL_NAMES = [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
    ]

    # Temporary errors: worth trying the next model for
    RETRYABLE_CODES = {429, 500, 503, 504}

    # Model not found / not available to this key: skip straight to next model
    SKIP_MODEL_CODES = {404}

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None

    # ---------------------------------------------------------------------------
    # Connect to Gemini
    # ---------------------------------------------------------------------------

    def create_client(self):
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing from .env")

        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key)

    # ---------------------------------------------------------------------------
    # Send the question and get a reply
    # ---------------------------------------------------------------------------

    def call_api(self, prompt: str) -> tuple:
        try:
            client = self.create_client()
        except ValueError as error:
            logger.error("Gemini client setup failed: %s", error)
            return "", ""

        for model_name in self.MODEL_NAMES:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                if response.text:
                    if model_name != self.MODEL_NAMES[0]:
                        logger.info("Used fallback model: %s", model_name)
                    return response.text.strip(), model_name

                logger.warning("%s returned an empty response.", model_name)

            except errors.APIError as error:
                code = getattr(error, "code", None)

                if code not in self.SKIP_MODEL_CODES and code not in self.RETRYABLE_CODES:
                    logger.error("Non-retryable Gemini error (%s): %s", code, error)
                    return "", ""

                logger.warning("%s failed (%s), trying next model.", model_name, code)

            except Exception as error:
                logger.warning("%s failed: %s", model_name, error)

        logger.error("All Gemini models failed.")     # Every model in the list was tried and none of them worked.
        return "", ""
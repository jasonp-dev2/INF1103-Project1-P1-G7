import logging
import os
from abc import ABC, abstractmethod
from datetime import date
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
logger = logging.getLogger(__name__)

class AIService(ABC):
    """Abstract Base Class (Interface) for AI service clients"""

    @abstractmethod
    def create_client(self):
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def call_api(self, prompt: str) -> tuple:
        pass



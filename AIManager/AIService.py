from abc import ABC, abstractmethod


class AIService(ABC):
    """Abstract Base Class (Interface) for AI service clients"""

    @abstractmethod
    def create_client(self) -> object:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def call_api(self, prompt: str) -> tuple:
        pass


from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def generate(self,prompt: str) -> str:
        """Send a prompt to AI and return its response as text."""
        pass
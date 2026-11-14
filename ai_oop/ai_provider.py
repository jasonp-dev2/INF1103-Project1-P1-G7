from abc import ABC, abstractmethod

class AIProvider(ABC):
    """The contract that every AI provider must implement."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def generate(self,prompt: str) -> str:
        pass
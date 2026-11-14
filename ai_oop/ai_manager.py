from .ai_provider import AIProvider

class AIManager:
    def __init__(self, provider: AIProvider):
        self._provider = provider

    @property
    def model_name(self) -> str:
        return self._provider.model_name
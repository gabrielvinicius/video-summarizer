# src/summarization/infrastructure/interfaces.py

from abc import ABC, abstractmethod


class ISummarizer(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the name of the summarization provider."""
        pass

    @abstractmethod
    async def summarize(self, text: str) -> str:
        pass

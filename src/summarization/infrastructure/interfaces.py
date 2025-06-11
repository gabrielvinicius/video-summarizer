# src/summarization/infrastructure/interfaces.py

from abc import ABC, abstractmethod


class ISummarizer(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> str:
        pass

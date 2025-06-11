# src/summarization/infrastructure/summarizer_interface.py
from abc import ABC, abstractmethod

class ISummarizer(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> str:
        ...

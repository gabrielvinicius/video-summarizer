# src/summarization/domain/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional

from src.summarization.domain.summary import Summary


class ISummaryRepository(ABC):
    @abstractmethod
    async def save(self, summary: Summary) -> Summary:
        """Saves a summary to the repository."""
        raise NotImplementedError

    @abstractmethod
    async def find_by_transcription_id(self, transcription_id: str) -> Optional[Summary]:
        """Finds a summary by its transcription ID."""
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, summary_id: str) -> Optional[Summary]:
        """Finds a summary by its ID."""
        raise NotImplementedError

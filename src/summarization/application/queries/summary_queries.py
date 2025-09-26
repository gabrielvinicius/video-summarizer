# src/summarization/application/queries/summary_queries.py
from typing import Optional
from uuid import UUID

from src.summarization.domain.interfaces import ISummaryRepository
from src.summarization.domain.summary import Summary


class SummaryQueries:
    """Handles all read-only operations for summaries."""
    def __init__(self, summary_repository: ISummaryRepository):
        self.summary_repository = summary_repository

    async def get_by_id(self, summary_id: str) -> Optional[Summary]:
        """Retrieves a summary by its unique ID."""
        return await self.summary_repository.find_by_id(summary_id)

    async def get_by_transcription_id(self, transcription_id: str) -> Optional[Summary]:
        """Retrieves a summary by its associated transcription ID."""
        return await self.summary_repository.find_by_transcription_id(transcription_id)

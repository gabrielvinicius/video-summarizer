# src/transcription/application/queries/transcription_queries.py
from typing import Optional
from uuid import UUID

from src.transcription.domain.transcription import Transcription
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository


class TranscriptionQueries:
    """Handles all read-only operations for transcriptions."""
    def __init__(self, transcription_repository: TranscriptionRepository):
        self.transcription_repository = transcription_repository

    async def get_by_id(self, transcription_id: str) -> Optional[Transcription]:
        """Retrieves a transcription by its unique ID."""
        return await self.transcription_repository.find_by_id(transcription_id)

    async def get_by_video_id(self, video_id: str) -> Optional[Transcription]:
        """Retrieves a transcription by its associated video ID."""
        return await self.transcription_repository.find_by_video_id(video_id)

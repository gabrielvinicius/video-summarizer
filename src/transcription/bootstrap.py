# src/transcription/bootstrap.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.transcription.application.queries.transcription_queries import TranscriptionQueries
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository

def bootstrap_transcription_module(db_session: AsyncSession) -> Dict[str, Any]:
    """Constructs and returns the query services for the transcription module."""
    transcription_repository = TranscriptionRepository(db=db_session)
    transcription_queries = TranscriptionQueries(transcription_repository=transcription_repository)

    return {
        "transcription_repository": transcription_repository,
        "transcription_queries": transcription_queries,
    }

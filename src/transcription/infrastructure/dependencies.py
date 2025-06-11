from typing import Any, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from .transcription_repository import TranscriptionRepository
from .whisper_speech_recognition import WhisperTranscriber


async def get_speech_recognition() -> ISpeechRecognition:
    return WhisperTranscriber()


async def get_transcription_repository(db: AsyncSession) -> TranscriptionRepository | None:
    if db:
        return TranscriptionRepository(db)
    return None

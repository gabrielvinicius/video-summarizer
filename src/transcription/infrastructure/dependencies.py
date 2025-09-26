from typing import Any, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

# Importação corrigida para o novo arquivo de interfaces
from src.transcription.infrastructure.interfaces import ISpeechRecognition
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from .huggingface_speech_recognition import HuggingfaceTranscriber
from .transcription_repository import TranscriptionRepository
from .whisper_speech_recognition import WhisperTranscriber


async def get_speech_recognition() -> ISpeechRecognition:
    return WhisperTranscriber()
    # return HuggingfaceTranscriber()


async def get_transcription_repository(db: AsyncSession) -> TranscriptionRepository | None:
    if db:
        return TranscriptionRepository(db)
    return None

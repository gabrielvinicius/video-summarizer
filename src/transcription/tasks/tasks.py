import asyncio
from typing import Union

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.events.event_bus import get_event_bus
from src.shared.infrastructure.database import get_db
from src.storage.infrastructure.dependencies import get_storage_service
from src.transcription.application.transcription_service import TranscriptionService, logger
from src.transcription.infrastructure.dependencies import get_transcription_repository, get_speech_recognition
from src.video_management.application.dependencies import get_video_service


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def process_transcription_task(self, video_id: str, language: str = "en"):
    """
    Celery async task to process video transcription.
    Accepts an optional language parameter.
    """
    try:
        return asyncio.run(_run_transcription(video_id, language))
    except Exception as e:
        logger.error(f"Error transcribing video {video_id}: {str(e)}", exc_info=True)
        return None


async def _run_transcription(video_id: str, language: str):
    """Helper to run transcription logic with dependency injection."""
    async for db_session in get_db():
        if not isinstance(db_session, AsyncSession):
            raise TypeError("Expected db_session to be an AsyncSession")

        storage_service = await get_storage_service()
        transcription_repository = await get_transcription_repository(db_session)
        video_service = await get_video_service(db_session)
        speech_recognition = await get_speech_recognition()

        service = TranscriptionService(
            event_bus=get_event_bus(),
            transcription_repository=transcription_repository,
            video_service=video_service,
            storage_service=storage_service,
            speech_recognition=speech_recognition
        )
        try:
            # Pass the language to the service method
            return await service.process_transcription(video_id=str(video_id), language=language)
        except Exception as e:
            logger.error(f"Error processing transcription for video {video_id}: {str(e)}", exc_info=True)
            raise

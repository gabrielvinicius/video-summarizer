import asyncio

from celery import shared_task

from src.storage.infrastructure.dependencies import get_storage_service
from src.transcription.application.dependencies import get_transcription_service
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.application.transcription_service import logger
from src.shared.infrastructure.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
from src.shared.events.event_bus import get_event_bus
from src.transcription.infrastructure.dependencies import get_transcription_repository, get_speech_recognition
from src.video_management.application.dependencies import get_video_service


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def process_transcription_task(self, video_id: str):
    """
    Celery async task to process video transcription.
    """
    try:
        return asyncio.run(_run_transcription(video_id))
        # return await _run_transcription(video_id)
    except Exception as e:
        # Optional: Uncomment to enable retries
        # raise self.retry(exc=e, countdown=60, max_retries=3)
        logger.error(f"Erro ao transcrever vídeo {video_id}: {str(e)}", exc_info=True)
        return None


async def _run_transcription(video_id: str):
    global db_session
    async for db_session in get_db():
        # Ensure db_session is an AsyncSession
        if not isinstance(db_session, AsyncSession):
            raise TypeError("Expected db_session to be an AsyncSession")
    storage_service = await get_storage_service()
    transcription_repository = await get_transcription_repository(db_session)
    video_service = await get_video_service(db_session)
    speech_recognition = await get_speech_recognition()  # Assuming this is defined in your dependencies

    service: TranscriptionService = TranscriptionService(event_bus=get_event_bus(),
                                                         transcription_repository=transcription_repository,
                                                         video_service=video_service,
                                                         storage_service=storage_service,
                                                         speech_recognition=speech_recognition   # Placeholder, replace with actual implementation
                                                         )
    try:
        return await service.process_transcription(str(video_id))
    except Exception as e:
        logger.error(f"Erro ao processar transcrição do vídeo {video_id}: {str(e)}", exc_info=True)
        raise

import asyncio

from celery import shared_task
from src.shared.infrastructure.database import AsyncSessionLocal  # Importa diretamente o sessionmaker

from src.shared.events.event_bus import get_event_bus
from src.storage.infrastructure.dependencies import get_storage_service
from src.transcription.application.transcription_service import logger, TranscriptionService
from src.transcription.infrastructure.dependencies import get_speech_recognition
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.video_management.infrastructure.video_repository import VideoRepository


@shared_task(bind=True)
def process_transcription_task(self, video_id: str):
    """
    Celery task for processing video transcriptions.
    """
    async def run_transcription():
        try:
            async with AsyncSessionLocal() as db:
                # Dependency injection
                event_bus = get_event_bus()
                storage_service = get_storage_service()
                speech_recognition = await get_speech_recognition()
                transcription_repo = TranscriptionRepository(db)
                video_repo = VideoRepository(db)

                # Service setup
                service = TranscriptionService(
                    speech_recognition=speech_recognition,
                    storage_service=storage_service,
                    event_bus=event_bus,
                    transcription_repository=transcription_repo,
                    video_repository=video_repo
                )

                return await service.process_transcription(video_id)

        except Exception as e:
            logger.error(f"Failed to process transcription for video {video_id}: {str(e)}", exc_info=True)
            raise e

    try:
        return asyncio.run(run_transcription())

    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)
        return None

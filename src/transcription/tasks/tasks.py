from celery import shared_task
from src.shared.infrastructure.database import AsyncSessionLocal


@shared_task(bind=True)
async def process_transcription_task(self, video_id: str):
    """
    Celery async task to process video transcription.
    """
    try:
        return await _run_transcription(video_id)
    except Exception as e:
        # Optional: Uncomment to enable retries
        # raise self.retry(exc=e, countdown=60, max_retries=3)
        from src.transcription.application.transcription_service import logger
        logger.error(f"Erro ao transcrever vídeo {video_id}: {str(e)}", exc_info=True)
        return None


async def _run_transcription(video_id: str):
    from src.shared.events.event_bus import get_event_bus
    from src.storage.infrastructure.dependencies import get_storage_service
    from src.transcription.application.transcription_service import TranscriptionService
    from src.transcription.infrastructure.dependencies import get_speech_recognition
    from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
    from src.video_management.infrastructure.video_repository import VideoRepository
    from src.transcription.application.transcription_service import logger

    async with AsyncSessionLocal() as db:
        service = TranscriptionService(
            speech_recognition=get_speech_recognition(),
            storage_service=get_storage_service(),
            event_bus=get_event_bus(),
            transcription_repository=TranscriptionRepository(db),
            video_repository=VideoRepository(db)
        )
        try:
            return await service.process_transcription(str(video_id))
        except Exception as e:
            logger.error(f"Erro ao processar transcrição do vídeo {video_id}: {str(e)}", exc_info=True)
            raise

from src.shared.events.event_bus import celery
import asyncio
from src.shared.infrastructure.database import AsyncSessionLocal


@celery.task(bind=True)
def process_transcription_task(self, video_id: str):
    try:
        return asyncio.run(_run_transcription(video_id))
    except Exception as e:
        # self.retry(exc=e, countdown=60, max_retries=0)
        return None


async def _run_transcription(video_id: str):
    from src.shared.events.event_bus import get_event_bus
    from src.storage.infrastructure.dependencies import get_storage_service
    from src.transcription.application.transcription_service import logger, TranscriptionService
    from src.transcription.infrastructure.dependencies import get_speech_recognition
    from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
    from src.video_management.infrastructure.video_repository import VideoRepository

    try:
        async with AsyncSessionLocal() as db:
            service = TranscriptionService(
                speech_recognition=get_speech_recognition(),
                storage_service=get_storage_service(),
                event_bus=get_event_bus(),
                transcription_repository=TranscriptionRepository(db),
                video_repository=VideoRepository(db)
            )
            return await service.process_transcription(video_id)
    except Exception as e:
        logger.error(f"Erro ao transcrever vídeo {video_id}: {str(e)}", exc_info=True)
        raise e

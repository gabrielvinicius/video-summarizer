import asyncio

from celery import shared_task
from src.transcription.application.dependencies import get_transcription_service


@shared_task(bind=True)
def process_transcription_task(self, video_id: str):
    """
    Celery async task to process video transcription.
    """
    try:
        return _run_transcription(video_id)
    except Exception as e:
        # Optional: Uncomment to enable retries
        # raise self.retry(exc=e, countdown=60, max_retries=3)
        from src.transcription.application.transcription_service import logger
        logger.error(f"Erro ao transcrever vídeo {video_id}: {str(e)}", exc_info=True)
        return None


def _run_transcription(video_id: str):
    from src.transcription.application.transcription_service import TranscriptionService
    from src.transcription.application.transcription_service import logger

    service: TranscriptionService = get_transcription_service()
    try:
        return  service.process_transcription(str(video_id))
    except Exception as e:
        logger.error(f"Erro ao processar transcrição do vídeo {video_id}: {str(e)}", exc_info=True)
        raise

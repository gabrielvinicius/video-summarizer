from celery import shared_task
from src.transcription.application.transcription_service import TranscriptionService
from src.shared.events.event_bus import get_event_bus
from src.transcription.infrastructure.whisper_speech_recognition import WhisperTranscriber
from src.storage.infrastructure.dependencies import get_storage_service
from src.shared.dependencies import get_video_repository, get_transcription_repository
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_transcription_task(self, video_id: str):
    """
    Celery task for processing video transcriptions.

    Args:
        video_id: ID of the video to process

    Note:
        - Uses synchronous Celery task wrapper around async operations
        - Handles dependency injection manually
        - Includes proper error handling and logging
    """
    try:
        # Initialize dependencies (sync call to async factories)
        event_bus = get_event_bus()
        storage_service = get_storage_service()
        speech_recognition = WhisperTranscriber()
        transcription_repo = get_transcription_repository()
        video_repo = get_video_repository()

        # Create service instance
        service = TranscriptionService(
            speech_recognition=speech_recognition,
            storage_service=storage_service,
            event_bus=event_bus,
            transcription_repository=transcription_repo,
            video_repository=video_repo
        )

        # Run async operation in event loop
        from asyncio import run
        return run(service.process_transcription(video_id))

    except Exception as e:
        logger.error(f"Failed to process transcription for video {video_id}: {str(e)}", exc_info=True)
        # Retry the task after 60 seconds if it fails
        self.retry(exc=e, countdown=60, max_retries=3)
        raise
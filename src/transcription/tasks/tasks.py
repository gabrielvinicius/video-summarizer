import asyncio
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.events.event_bus import get_event_bus
from src.shared.infrastructure.database import get_db
from src.storage.infrastructure.dependencies import get_storage_service_factory
from src.transcription.application.transcription_service import TranscriptionService, logger
from src.transcription.infrastructure.dependencies import get_transcription_repository, create_speech_recognition_service
from src.video_management.application.video_service import VideoService
from src.video_management.infrastructure.video_repository import VideoRepository
from src.metrics.application.metrics_service import MetricsService
from src.metrics.infrastructure.prometheus_provider import PrometheusMetricsProvider


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def process_transcription_task(self, video_id: str, provider: str, language: str = "en"):
    """
    Celery async task to process video transcription with a specific provider.
    """
    try:
        return asyncio.run(_run_transcription(video_id, provider, language))
    except Exception as e:
        logger.error(f"Error transcribing video {video_id}: {str(e)}", exc_info=True)
        return None


async def _run_transcription(video_id: str, provider: str, language: str):
    """Helper to run transcription logic with dynamic dependency injection."""
    async for db_session in get_db():
        if not isinstance(db_session, AsyncSession):
            raise TypeError("Expected db_session to be an AsyncSession")

        # --- Manual Dependency Injection for Celery Task ---
        event_bus = get_event_bus()
        metrics_provider = PrometheusMetricsProvider()
        metrics_service = MetricsService(provider=metrics_provider)
        
        # Video and Storage services
        video_repository = VideoRepository(db=db_session)
        storage_service_factory = get_storage_service_factory()
        video_service = VideoService(
            storage_service_factory=storage_service_factory,
            event_bus=event_bus,
            video_repository=video_repository,
            metrics_service=metrics_service
        )

        video = await video_service.get_video_by_id(video_id)
        if not video:
            logger.error(f"Video {video_id} not found in transcription task.")
            return

        # Dynamically create the correct storage and speech recognition services
        storage_service = storage_service_factory(video.storage_provider)
        speech_recognition_service = create_speech_recognition_service(provider)
        transcription_repository = await get_transcription_repository(db_session)

        service = TranscriptionService(
            speech_recognition=speech_recognition_service,
            storage_service=storage_service,
            event_bus=event_bus,
            transcription_repository=transcription_repository,
            video_service=video_service,
            metrics_service=metrics_service
        )
        
        try:
            return await service.process_transcription(video_id=str(video_id), provider=provider, language=language)
        except Exception as e:
            logger.error(f"Error processing transcription for video {video_id}: {str(e)}", exc_info=True)
            raise

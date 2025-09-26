# src/video_management/application/commands/upload_video_command_handler.py
import time
from uuid import uuid4
import structlog

from src.metrics.application.metrics_service import MetricsService
from src.shared.events.domain_events import VideoUploaded
from src.shared.events.event_bus import EventBus
from src.storage.infrastructure.dependencies import StorageServiceFactory
from src.video_management.domain.video import Video, VideoStatus
from src.video_management.infrastructure.video_repository import VideoRepository
from .upload_video_command import UploadVideoCommand

logger = structlog.get_logger(__name__)


class UploadVideoCommandHandler:
    def __init__(
        self,
        storage_service_factory: StorageServiceFactory,
        event_bus: EventBus,
        video_repository: VideoRepository,
        metrics_service: MetricsService,
    ):
        self.storage_service_factory = storage_service_factory
        self.event_bus = event_bus
        self.video_repository = video_repository
        self.metrics_service = metrics_service

    async def handle(self, command: UploadVideoCommand) -> Video:
        """Handles the video upload process."""
        start_time = time.time()
        video_id = uuid4()
        storage_service = self.storage_service_factory(command.storage_provider)

        try:
            file_path = f"videos/{command.user_id}/{video_id}/{command.filename}"
            logger.info("video_upload.started", video_id=str(video_id), provider=command.storage_provider)

            await storage_service.upload(file_path, command.file)

            video = Video(
                id=video_id,
                user_id=command.user_id,
                file_path=file_path,
                status=VideoStatus.UPLOADED,
                storage_provider=command.storage_provider
            )
            saved_video = await self.video_repository.save(video)

            event = VideoUploaded(video_id=str(video_id), user_id=command.user_id)
            await self.event_bus.publish(event)

            duration = time.time() - start_time
            logger.info("video_upload.completed", video_id=str(video_id), duration=duration)

            self.metrics_service.increment_video_upload('success')
            self.metrics_service.observe_upload_duration(
                video_id=str(video_id),
                duration=duration,
                provider=storage_service.provider_name
            )

            return saved_video

        except Exception as e:
            self.metrics_service.increment_video_upload('failure')
            logger.error("video_upload.failed", video_id=str(video_id), error=str(e))
            if 'file_path' in locals():
                try:
                    await storage_service.delete(file_path)
                except Exception as cleanup_error:
                    logger.error("video_upload.cleanup_failed", video_id=str(video_id), error=str(cleanup_error))
            raise ValueError(f"Video upload failed: {str(e)}") from e

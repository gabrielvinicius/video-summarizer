# src/video_management/application/video_service.py
from typing import Optional
from uuid import UUID
import structlog

from src.shared.events.domain_events import TranscriptionRequested
from src.shared.events.event_bus import EventBus
from src.storage.infrastructure.dependencies import StorageServiceFactory
from src.video_management.domain.video import Video, VideoStatus
from src.video_management.infrastructure.video_repository import VideoRepository
# CQRS imports
from .commands.upload_video_command import UploadVideoCommand
from .commands.upload_video_command_handler import UploadVideoCommandHandler
from .queries.video_queries import VideoQueries

logger = structlog.get_logger(__name__)


class VideoService:
    """Acts as a facade for video-related operations, dispatching commands."""
    def __init__(
        self,
        upload_video_handler: UploadVideoCommandHandler,
        video_repository: VideoRepository,
        storage_service_factory: StorageServiceFactory,
        video_queries: VideoQueries,
        event_bus: EventBus,
    ):
        self.upload_video_handler = upload_video_handler
        self.video_repository = video_repository
        self.storage_service_factory = storage_service_factory
        self.video_queries = video_queries
        self.event_bus = event_bus

    async def create_video(self, command: UploadVideoCommand) -> Video:
        """Dispatches the UploadVideoCommand to its handler."""
        return await self.upload_video_handler.handle(command)

    async def request_transcription(self, video_id: str, provider: str):
        """Validates and dispatches a transcription request event."""
        video = await self.video_queries.get_by_id(video_id)
        if not video:
            raise ValueError(f"Video with id {video_id} not found.")

        if video.status == VideoStatus.PROCESSING:
            raise ValueError("A transcription for this video is already in progress.")

        event = TranscriptionRequested(video_id=str(video.id), provider=provider)
        await self.event_bus.publish(event)

    # --- Mixed Command/Query Methods (To be refactored) ---
    async def delete_video(self, video_id: str) -> bool:
        video = await self.video_repository.find_by_id(UUID(video_id))
        if not video:
            return False
        try:
            storage_service = self.storage_service_factory(video.storage_provider)
            await storage_service.delete(video.file_path)
        except Exception as e:
            logger.error(f"Failed to delete video file from storage: {str(e)}")
        return await self.video_repository.delete(UUID(video_id))

    async def get_video_streaming_url(self, video_id: str) -> Optional[str]:
        video = await self.video_queries.get_by_id(video_id)
        if not video or not video.storage_provider:
            return None
        try:
            storage_service = self.storage_service_factory(video.storage_provider)
            url, _ = await storage_service.download(video.file_path)
            return url
        except Exception as e:
            logger.error(f"Failed to get streaming URL: {str(e)}")
            return None

# src/video_management/application/video_service.py
from typing import Optional
from uuid import UUID
import structlog

from src.storage.infrastructure.dependencies import StorageServiceFactory
from src.video_management.domain.video import Video, VideoStatus
from src.video_management.infrastructure.video_repository import VideoRepository
# CQRS imports
from .commands.upload_video_command import UploadVideoCommand
from .commands.upload_video_command_handler import UploadVideoCommandHandler

logger = structlog.get_logger(__name__)


class VideoService:
    """Acts as a facade for video-related operations, dispatching commands."""
    def __init__(
        self,
        upload_video_handler: UploadVideoCommandHandler,
        video_repository: VideoRepository, # Still needed for mixed operations
        storage_service_factory: StorageServiceFactory, # Still needed for mixed operations
    ):
        self.upload_video_handler = upload_video_handler
        self.video_repository = video_repository
        self.storage_service_factory = storage_service_factory

    # --- Command Dispatcher ---
    async def create_video(self, command: UploadVideoCommand) -> Video:
        """Dispatches the UploadVideoCommand to its handler."""
        return await self.upload_video_handler.handle(command)

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
        # This method reads data to create the URL, so it's query-like.
        # It will be moved to VideoQueries in a future refactoring.
        video = await self.video_repository.find_by_id(UUID(video_id))
        if not video or not video.storage_provider:
            return None
        try:
            storage_service = self.storage_service_factory(video.storage_provider)
            url, _ = await storage_service.download(video.file_path)
            return url
        except Exception as e:
            logger.error(f"Failed to get streaming URL: {str(e)}")
            return None

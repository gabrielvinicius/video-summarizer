import time
from typing import Optional, Sequence
from uuid import uuid4, UUID

import structlog

from src.metrics.application.metrics_service import MetricsService
from src.shared.events.domain_events import VideoUploaded
from src.shared.events.event_bus import EventBus
from src.storage.application.storage_service import StorageService
from src.video_management.domain.video import Video, VideoStatus
from src.video_management.infrastructure.video_repository import VideoRepository

logger = structlog.get_logger(__name__)

class VideoService:
    def __init__(
            self,
            storage_service: StorageService,
            event_bus: EventBus,
            video_repository: VideoRepository,
            metrics_service: MetricsService,
    ):
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.video_repository = video_repository
        self.metrics_service = metrics_service

    async def upload_video(self, user_id: str, file: bytes, filename: str) -> Video:
        start_time = time.time()
        video_id = uuid4()
        try:
            file_path = f"videos/{user_id}/{video_id}/{filename}"
            logger.info("video_upload.started", video_id=str(video_id), user_id=user_id, filename=filename)

            if self.storage_service is None:
                raise RuntimeError("Storage service is not configured.")

            await self.storage_service.upload(file_path, file)

            video = Video(
                id=video_id,
                user_id=user_id,
                file_path=file_path,
                status=VideoStatus.UPLOADED
            )
            saved_video = await self.video_repository.save(video)

            event = VideoUploaded(video_id=str(video_id), user_id=user_id)
            await self.event_bus.publish(event)

            duration = time.time() - start_time
            logger.info("video_upload.completed", video_id=str(video_id), duration=duration)
            
            # Observe metrics with the provider label
            self.metrics_service.increment_video_upload('success')
            self.metrics_service.observe_upload_duration(
                video_id=str(video_id),
                duration=duration,
                provider=self.storage_service.provider_name
            )

            return saved_video

        except Exception as e:
            self.metrics_service.increment_video_upload('failure')
            logger.error("video_upload.failed", video_id=str(video_id), error=str(e))
            if 'file_path' in locals():
                try:
                    await self.storage_service.delete(file_path)
                except Exception as cleanup_error:
                    logger.error("video_upload.cleanup_failed", video_id=str(video_id), error=str(cleanup_error))
            raise ValueError(f"Video upload failed: {str(e)}") from e

    async def get_video_by_id(self, video_id: str) -> Optional[Video]:
        return await self.video_repository.find_by_id(UUID(video_id))

    async def get_video_by_user_by_id(self, video_id: str, user_id: str) -> Optional[Video]:
        return await self.video_repository.find_by_id_by_user(video_id=UUID(video_id), user_id=UUID(user_id))

    async def list_all_videos(self, skip: int = 0, limit: int = 100) -> Sequence[Video]:
        return await self.video_repository.list_all(skip, limit)

    async def list_user_videos(self, user_id: str, skip=0, limit=100) -> Sequence[Video]:
        return await self.video_repository.list_by_user(UUID(user_id))

    async def update_video_status(self, video_id: str, status: VideoStatus)-> Optional[Video]:
        video = await self.video_repository.find_by_id(UUID(video_id))
        if not video:
            return None
        video.status = status
        return await self.video_repository.save(video)

    async def delete_video(self, video_id: str) -> bool:
        video = await self.video_repository.find_by_id(UUID(video_id))
        if not video:
            return False
        try:
            await self.storage_service.delete(video.file_path)
        except Exception as e:
            logger.error(f"Failed to delete video file: {str(e)}")
        return await self.video_repository.delete(UUID(video_id))

    async def get_video_streaming_url(self, video_id: str) -> Optional[str]:
        video = await self.get_video_by_id(video_id)
        if not video or video.status != VideoStatus.COMPLETED:
            return None
        try:
            # In a real scenario, this would generate a presigned URL
            # For now, we assume the download method can provide a URL or content
            url, _ = await self.storage_service.download(video.file_path)
            return url
        except Exception as e:
            logger.error(f"Failed to get streaming URL: {str(e)}")
            return None

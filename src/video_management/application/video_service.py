from uuid import uuid4
from typing import Optional, Sequence
from src.video_management.domain.video import Video, VideoStatus
from src.storage.application.storage_service import StorageService
from src.video_management.infrastructure.video_repository import VideoRepository
from src.shared.events.event_bus import EventBus
import logging

logger = logging.getLogger(__name__)


class VideoService:
    def __init__(
            self,
            storage_service: StorageService,
            event_bus: EventBus,
            video_repository: VideoRepository
    ):
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.video_repository = video_repository

    async def upload_video(self, user_id: str, file: bytes, filename: str) -> Video:
        """Uploads a video and triggers processing event"""
        try:
            video_id = uuid4()
            file_path = f"videos/{user_id}/{video_id}/{filename}"

            if self.storage_service is None:
                raise RuntimeError("Storage service is None!")

            print(f"Storage service: {self.storage_service}")
            print(f"Has 'upload': {hasattr(self.storage_service, 'upload')}")
            print(f"Upload method: {self.storage_service.upload}")

            # Upload file to storage
            await self.storage_service.upload(file_path, file)

                # Create video entity
            video = Video(
                id=video_id,
                user_id=user_id,
                file_path=file_path,
                status=VideoStatus.UPLOADED
            )

                # Save to database
            saved_video = await self.video_repository.save(video)
            if not saved_video:
                raise ValueError("Failed to save video to database")

                # Publish event
            self.event_bus.publish("video_uploaded", {
                "video_id": video_id,
                "file_path": file_path,
                "user_id": user_id
            })

            return saved_video

        except Exception as e:
            logger.error(f"Failed to upload video: {str(e)}")

            # Cleanup if upload failed
            if 'file_path' in locals():
                try:
                    await self.storage_service.delete(file_path)
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {str(cleanup_error)}")

            raise ValueError(f"Video upload failed: {str(e)}") from e

    async def get_video_by_id(self, video_id: str) -> Optional[Video]:
        return await self.video_repository.find_by_id(video_id)

    async def list_all_videos(self, skip: int = 0, limit: int = 100) -> Sequence[Video]:
        return await self.video_repository.list_all(skip, limit)

    async def list_user_videos(self, user_id: str) -> Sequence[Video]:
        return await self.video_repository.list_by_user(user_id)

    async def update_video_status(self, video_id: str, status: VideoStatus) -> Optional[Video]:
        """Updates video status and returns updated video"""
        video = await self.video_repository.find_by_id(video_id)
        if not video:
            return None

        video.status = status
        return await self.video_repository.save(video)

    async def delete_video(self, video_id: str) -> bool:
        """Deletes video and its storage files"""
        video = await self.video_repository.find_by_id(video_id)
        if not video:
            return False

        # Delete from storage first
        try:
            await self.storage_service.delete(video.file_path)
        except Exception as e:
            logger.error(f"Failed to delete video file: {str(e)}")
            # Continue with database deletion even if storage fails

        # Delete from database
        return await self.video_repository.delete(video_id)

    async def get_video_streaming_url(self, video_id: str) -> Optional[str]:
        """Generates streaming URL for processed videos"""
        video = await self.get_video_by_id(video_id)
        if not video or video.status != VideoStatus.COMPLETED:
            return None

        try:
            return await self.storage_service.download(video.file_path)
        except Exception as e:
            logger.error(f"Failed to get streaming URL: {str(e)}")
            return None
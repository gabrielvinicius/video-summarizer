from uuid import uuid4
from datetime import datetime
from typing import Optional, Sequence
from src.video_management.domain.video import Video, VideoStatus
from src.storage.application.storage_service import StorageService
from src.video_management.infrastructure.video_repository import VideoRepository
from src.shared.events.event_bus import EventBus


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
        video_id = str(uuid4())
        file_path = f"videos/{user_id}/{video_id}/{filename}"

        await self.storage_service.upload(file_path, file)

        video = Video(
            id=video_id,
            user_id=user_id,
            file_path=file_path,
            status=VideoStatus.UPLOADED
        )
        await self.video_repository.save(video)

        await self.event_bus.publish("video_uploaded", {
            "video_id": video_id,
            "file_path": file_path,
            "user_id": user_id
        })

        return video

    async def get_video_by_id(self, video_id: str) -> Optional[Video]:
        return await self.video_repository.find_by_id(video_id)

    async def list_all_videos(self, skip: int = 0, limit: int = 100) -> Sequence[Video]:
        return await self.video_repository.list_all(skip, limit)

    async def list_user_videos(self, user_id: str) -> Sequence[Video]:
        return await self.video_repository.list_by_user(user_id)

    async def update_video_status(self, video_id: str, status: VideoStatus) -> Optional[Video]:
        """Updates video status and returns updated video"""
        return await self.video_repository.update_status(video_id, status)

    async def delete_video(self, video_id: str) -> bool:
        """Deletes video and its storage files"""
        video = await self.video_repository.find_by_id(video_id)
        if not video:
            return False

        # Delete from storage
        try:
            await self.storage_service.delete(video.file_path)
        except Exception as e:
            # Handle storage deletion errors (log, retry, etc.)
            pass

        # Delete from database
        return await self.video_repository.delete(video_id)

    async def get_video_streaming_url(self, video_id: str) -> Optional[str]:
        """Generates streaming URL for processed videos"""
        video = await self.get_video_by_id(video_id)

        if not video or video.status != VideoStatus.COMPLETED:
            return None

        return await self.storage_service.download(video.file_path)
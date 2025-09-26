# src/video_management/application/queries/video_queries.py
from typing import Optional, Sequence
from uuid import UUID

from src.video_management.domain.video import Video
from src.video_management.infrastructure.video_repository import VideoRepository


class VideoQueries:
    """Handles all read-only operations for videos."""
    def __init__(self, video_repository: VideoRepository):
        self.video_repository = video_repository

    async def get_video_by_id(self, video_id: str) -> Optional[Video]:
        return await self.video_repository.find_by_id(UUID(video_id))

    async def get_video_by_user_by_id(self, video_id: str, user_id: str) -> Optional[Video]:
        return await self.video_repository.find_by_id_by_user(video_id=UUID(video_id), user_id=UUID(user_id))

    async def list_user_videos(self, user_id: str, skip: int = 0, limit: int = 100) -> Sequence[Video]:
        return await self.video_repository.list_by_user(user_id=UUID(user_id), skip=skip, limit=limit)

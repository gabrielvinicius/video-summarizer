# tests/mocks/in_memory_video_repository.py
from typing import Dict, Optional, List
from uuid import UUID

from src.video_management.domain.video import Video


class InMemoryVideoRepository:
    def __init__(self):
        self.videos: Dict[str, Video] = {}

    async def save(self, video: Video) -> Video:
        self.videos[str(video.id)] = video
        return video

    async def find_by_id(self, video_id: UUID) -> Optional[Video]:
        return self.videos.get(str(video_id))

    def clear(self):
        self.videos.clear()

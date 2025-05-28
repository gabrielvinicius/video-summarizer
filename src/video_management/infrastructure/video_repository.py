from sqlalchemy import select, Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import Session
from src.video_management.domain.video import Video,VideoStatus
from typing import Optional, Any, Sequence


class VideoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, video: Video) -> Video:
        self.db.add(video)
        await self.db.commit()
        await self.db.refresh(video)
        return video

    async def find_by_id(self, video_id: str) -> Optional[Video]:
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[Video]:
        result = await self.db.execute(select(Video).offset(skip).limit(limit))
        return result.scalars().all()

    async def list_by_user(self, user_id: str) -> Sequence[Video]:
        result = await self.db.execute(select(Video).where(Video.user_id == user_id))
        return result.scalars().all()

    async def update_status(self, video_id: str, status: VideoStatus):
        video = self.find_by_id(video_id)
        if video:
            video.status = status
            await self.db.commit()

    async def delete(self, video_id: str) -> bool:
        video = await self.find_by_id(video_id)
        if not video:
            return False
        await self.db.delete(video)
        await self.db.commit()
        return True

    async def exists(self, video_id: str) -> bool:
        video = await self.find_by_id(video_id)
        return video is not None
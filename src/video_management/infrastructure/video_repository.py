from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.video_management.domain.video import Video, VideoStatus
from typing import Optional, Sequence


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

    async def update_status(self, video_id: str, status: VideoStatus) -> Optional[Video]:
        video = await self.find_by_id(video_id)  # Fixed: added await
        if video:
            video.status = status
            await self.db.commit()
            await self.db.refresh(video)  # Ensure refreshed state
            return video
        return None

    async def delete(self, video_id: str) -> bool:
        video = await self.find_by_id(video_id)
        if not video:
            return False
        await self.db.delete(video)
        await self.db.commit()
        return True

    async def exists(self, video_id: str) -> bool:
        # Optimized existence check
        stmt = select(select(Video).where(Video.id == video_id).exists())
        result = await self.db.execute(stmt)
        return result.scalar()
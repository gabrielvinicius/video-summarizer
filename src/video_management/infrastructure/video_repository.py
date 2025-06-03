from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.video_management.domain.video import Video, VideoStatus
from typing import Optional, Sequence, List
import logging

logger = logging.getLogger(__name__)


class VideoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, video: Video) -> Video:
        """Saves a video entity and returns the persisted version."""
        try:
            self.db.add(video)
            await self.db.commit()
            await self.db.refresh(video)
            return video
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save video {video.id}: {e}")
            raise

    async def find_by_id(self, video_id: str) -> Optional[Video]:
        """Finds a video by ID, optionally including user relationship."""
        query = select(Video).where(Video.id == video_id)
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[VideoStatus] = None
    ) -> Sequence[Video]:
        """Lists videos with pagination and optional status filter."""
        query = select(Video).offset(skip).limit(limit)
        if status:
            query = query.where(Video.status == status)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[VideoStatus] = None
    ) -> Sequence[Video]:
        """Lists videos for a specific user with pagination and status filter."""
        query = select(Video).where(Video.user_id == user_id)
        if status:
            query = query.where(Video.status == status)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_status(self, video_id: str, status: VideoStatus) -> Optional[Video]:
        """Updates video status efficiently and returns the updated video."""
        try:
            stmt = (
                update(Video)
                .where(Video.id == video_id)
                .values(status=status)
                .returning(Video)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update status for video {video_id}: {e}")
            raise

    async def bulk_update_status(self, video_ids: List[str], status: VideoStatus) -> int:
        """Updates status for multiple videos in a single operation."""
        try:
            result = await self.db.execute(
                update(Video)
                .where(Video.id.in_(video_ids))
                .values(status=status)
            )
            await self.db.commit()
            return result.rowcount
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Bulk status update failed: {e}")
            raise

    async def delete(self, video_id: str) -> bool:
        """Deletes a video and returns whether operation was successful."""
        try:
            result = await self.db.execute(
                delete(Video).where(Video.id == video_id)
            )
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete video {video_id}: {e}")
            raise

    async def exists(self, video_id: str) -> bool:
        """Efficiently checks if a video exists."""
        result = await self.db.execute(
            select(select(Video).where(Video.id == video_id).exists())
        )
        return result.scalar()

    async def count_by_user(self, user_id: str, status: Optional[VideoStatus] = None) -> int:
        """Counts videos for a user, optionally filtered by status."""
        query = select(func.count(Video.id)).where(Video.user_id == user_id)
        if status:
            query = query.where(Video.status == status)
        result = await self.db.execute(query)
        return result.scalar_one()  # Always returns an integer

    async def get_video_status(self, video_id: str) -> Optional[VideoStatus]:
        """Retrieves just the status of a video without loading entire entity."""
        result = await self.db.execute(
            select(Video.status).where(Video.id == video_id)
        )
        return result.scalar_one_or_none()
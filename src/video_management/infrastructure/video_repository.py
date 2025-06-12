from typing import Optional, Sequence, List, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update, func
from src.video_management.domain.video import Video, VideoStatus
import logging

logger = logging.getLogger(__name__)

class VideoRepository:
    def __init__(self, db: Union[AsyncSession, Session]):
        self.db = db

    def _is_async(self):
        return isinstance(self.db, AsyncSession)

    async def save(self, video: Video) -> Video:
        """Saves a video entity and returns the persisted version."""
        try:
            self.db.add(video)
            if self._is_async():
                await self.db.commit()
                await self.db.refresh(video)
            else:
                self.db.commit()
                self.db.refresh(video)
            return video
        except Exception as e:
            if self._is_async():
                await self.db.rollback()
            else:
                self.db.rollback()
            logger.error(f"Failed to save video {getattr(video, 'id', None)}: {e}")
            raise

    async def find_by_id(self, video_id: UUID) -> Optional[Video]:
        """Finds a video by ID."""
        query = select(Video).where(Video.id == video_id)
        if self._is_async():
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        else:
            result = self.db.execute(query)
            return result.scalar_one_or_none()

    async def find_by_id_by_user(self, video_id: UUID, user_id: UUID) -> Optional[Video]:
        """Finds a video by ID."""
        query = select(Video).where(Video.id == video_id).where(Video.user_id == user_id)
        if self._is_async():
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        else:
            result = self.db.execute(query)
            return result.scalar_one_or_none()

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
        if self._is_async():
            result = await self.db.execute(query)
            return result.scalars().all()
        else:
            result = self.db.execute(query)
            return result.scalars().all()

    async def list_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[VideoStatus] = None
    ) -> Sequence[Video]:
        """Lists videos for a specific user with pagination and status filter."""
        query = select(Video).where(Video.user_id == user_id)
        if status:
            query = query.where(Video.status == status)
        query = query.offset(skip).limit(limit)
        if self._is_async():
            result = await self.db.execute(query)
            return result.scalars().all()
        else:
            result = self.db.execute(query)
            return result.scalars().all()

    async def update_status(self, video_id: UUID, status: VideoStatus) -> Optional[Video]:
        """Updates video status efficiently and returns the updated video."""
        try:
            stmt = (
                update(Video)
                .where(Video.id == video_id)
                .values(status=status)
                .returning(Video)
            )
            if self._is_async():
                result = await self.db.execute(stmt)
                await self.db.commit()
                return await result.scalar_one_or_none()
            else:
                result = self.db.execute(stmt)
                self.db.commit()
                return result.scalar_one_or_none()
        except Exception as e:
            if self._is_async():
                await self.db.rollback()
            else:
                self.db.rollback()
            logger.error(f"Failed to update status for video {video_id}: {e}")
            raise

    async def bulk_update_status(self, video_ids: List[UUID], status: VideoStatus) -> int:
        """Updates status for multiple videos in a single operation."""
        try:
            stmt = (
                update(Video)
                .where(Video.id.in_(video_ids))
                .values(status=status)
            )
            if self._is_async():
                result = await self.db.execute(stmt)
                await self.db.commit()
                return result.rowcount
            else:
                result = self.db.execute(stmt)
                self.db.commit()
                return result.rowcount
        except Exception as e:
            if self._is_async():
                await self.db.rollback()
            else:
                self.db.rollback()
            logger.error(f"Bulk status update failed: {e}")
            raise

    async def delete(self, video_id: UUID) -> bool:
        """Deletes a video and returns whether operation was successful."""
        try:
            stmt = delete(Video).where(Video.id == video_id)
            if self._is_async():
                result = await self.db.execute(stmt)
                await self.db.commit()
                return result.rowcount > 0
            else:
                result = self.db.execute(stmt)
                self.db.commit()
                return result.rowcount > 0
        except Exception as e:
            if self._is_async():
                await self.db.rollback()
            else:
                self.db.rollback()
            logger.error(f"Failed to delete video {video_id}: {e}")
            raise

    async def exists(self, video_id: UUID) -> bool:
        """Efficiently checks if a video exists."""
        stmt = select(select(Video).where(Video.id == video_id).exists())
        if self._is_async():
            result = await self.db.execute(stmt)
            return result.scalar()
        else:
            result = self.db.execute(stmt)
            return result.scalar()

    async def count_by_user(self, user_id: UUID, status: Optional[VideoStatus] = None) -> int:
        """Counts videos for a user, optionally filtered by status."""
        query = select(func.count(Video.id)).where(Video.user_id == user_id)
        if status:
            query = query.where(Video.status == status)
        if self._is_async():
            result = await self.db.execute(query)
            return result.scalar_one()
        else:
            result = self.db.execute(query)
            return result.scalar_one()

    async def get_video_status(self, video_id: UUID) -> Optional[VideoStatus]:
        """Retrieves just the status of a video without loading entire entity."""
        stmt = select(Video.status).where(Video.id == video_id)
        if self._is_async():
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        else:
            result = self.db.execute(stmt)
            return result.scalar_one_or_none()
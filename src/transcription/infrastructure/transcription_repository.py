from typing import Sequence, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from src.transcription.domain.transcription import Transcription
from src.video_management.domain.video import Video
import logging

logger = logging.getLogger(__name__)

class TranscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, transcription_id: str) -> Optional[Transcription]:
        """Finds a transcription by its ID."""
        result = await self.db.execute(
            select(Transcription)
            .where(Transcription.id == transcription_id)
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def save(self, transcription: Transcription) -> Transcription:
        """Saves a transcription entity."""
        try:
            self.db.add(transcription)
            await self.db.commit()
            await self.db.refresh(transcription)
            return transcription

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save video {transcription.id}: {e}")
            raise

    async def list_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> Sequence[Transcription]:
        result = await self.db.execute(
            select(Transcription)
            .join(Video, Transcription.video_id == Video.id)
            .where(Video.user_id == user_id)
            .order_by(Transcription.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def delete(self, transcription_id: str) -> bool:
        """Deletes a transcription by ID."""
        async with self.db.begin_nested():
            stmt = (
                delete(Transcription)
                .where(Transcription.id == transcription_id)
                .returning(Transcription.id)
            )
            result = await self.db.execute(stmt)
            deleted = result.scalar() is not None
            # No need to commit here
            return deleted

    async def find_by_video_id(self, video_id: str) -> Optional[Transcription]:
        """Finds transcription by associated video ID."""
        result = await self.db.execute(
            select(Transcription)
            .where(Transcription.video_id == video_id)
        )
        return result.scalar_one_or_none()

    async def exists(self, transcription_id: UUID) -> bool:
        """Checks if a transcription exists."""
        stmt = select(select(Transcription)
            .where(Transcription.id == transcription_id)
            .exists()
        )
        result = await self.db.execute(stmt)
        return result.scalar()
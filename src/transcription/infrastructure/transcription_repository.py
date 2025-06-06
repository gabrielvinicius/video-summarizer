from typing import Sequence, Optional, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.transcription.domain.transcription import Transcription
import logging

logger = logging.getLogger(__name__)


class TranscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, transcription_id: Union[str, UUID]) -> Optional[Transcription]:
        result = await self.db.execute(
            select(Transcription)
            .where(Transcription.id == str(transcription_id))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def save(self, transcription: Transcription) -> Transcription:
        try:
            self.db.add(transcription)
            await self.db.commit()
            await self.db.refresh(transcription)
            return transcription
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save transcription {transcription.id}: {e}")
            raise

    # async def list_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> Sequence[Transcription]:
    #     ...
    #     return result.scalars().all()

    async def delete(self, transcription_id: Union[str, UUID]) -> bool:
        async with self.db.begin_nested():
            stmt = (
                delete(Transcription)
                .where(Transcription.id == str(transcription_id))
                .returning(Transcription.id)
            )
            result = await self.db.execute(stmt)
            deleted = result.scalar() is not None
            return deleted

    async def find_by_video_id(self, video_id: Union[str, UUID]) -> Optional[Transcription]:
        result = await self.db.execute(
            select(Transcription)
            .where(Transcription.video_id == str(video_id))
        )
        return result.scalar_one_or_none()

    async def exists(self, transcription_id: Union[str, UUID]) -> bool:
        stmt = select(Transcription).where(Transcription.id == str(transcription_id)).exists()
        result = await self.db.execute(select(stmt))
        return result.scalar()

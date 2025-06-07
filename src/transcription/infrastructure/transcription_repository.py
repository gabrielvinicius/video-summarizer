from typing import Sequence, Optional, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from src.transcription.domain.transcription import Transcription
import logging
import asyncio

logger = logging.getLogger(__name__)

class TranscriptionRepository:
    def __init__(self, db: Union[Session, AsyncSession]):
        self.db = db

    def _is_async(self):
        return isinstance(self.db, AsyncSession)

    async def find_by_id(self, transcription_id: Union[str, UUID]) -> Optional[Transcription]:
        stmt = select(Transcription).where(Transcription.id == str(transcription_id)).execution_options(populate_existing=True)
        if self._is_async():
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        else:
            result = self.db.execute(stmt)
            return result.scalar_one_or_none()

    async def save(self, transcription: Transcription) -> Transcription:
        try:
            self.db.add(transcription)
            if self._is_async():
                await self.db.commit()
                await self.db.refresh(transcription)
            else:
                self.db.commit()
                self.db.refresh(transcription)
            return transcription
        except Exception as e:
            if self._is_async():
                await self.db.rollback()
            else:
                self.db.rollback()
            logger.error(f"Failed to save transcription {transcription.id}: {e}")
            raise

    async def delete(self, transcription_id: Union[str, UUID]) -> bool:
        stmt = delete(Transcription).where(Transcription.id == str(transcription_id)).returning(Transcription.id)
        if self._is_async():
            async with self.db.begin_nested():
                result = await self.db.execute(stmt)
                deleted = result.scalar() is not None
                return deleted
        else:
            with self.db.begin_nested():
                result = self.db.execute(stmt)
                deleted = result.scalar() is not None
                return deleted

    async def find_by_video_id(self, video_id: Union[str, UUID]) -> Optional[Transcription]:
        stmt = select(Transcription).where(Transcription.video_id == str(video_id))
        if self._is_async():
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        else:
            result = self.db.execute(stmt)
            return result.scalar_one_or_none()

    async def exists(self, transcription_id: Union[str, UUID]) -> bool:
        stmt = select(Transcription).where(Transcription.id == str(transcription_id)).exists()
        query = select(stmt)
        if self._is_async():
            result = await self.db.execute(query)
            return result.scalar()
        else:
            result = self.db.execute(query)
            return result.scalar()
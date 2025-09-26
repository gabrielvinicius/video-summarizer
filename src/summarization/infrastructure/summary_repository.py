# src/summarization/infrastructure/summary_repository.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.summarization.domain.interfaces import ISummaryRepository
from src.summarization.domain.summary import Summary


class SummaryRepository(ISummaryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, summary: Summary) -> Summary:
        self.session.add(summary)
        await self.session.commit()
        await self.session.refresh(summary)
        return summary

    async def find_by_transcription_id(self, transcription_id: str) -> Optional[Summary]:
        stmt = select(Summary).where(Summary.transcription_id == transcription_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id(self, summary_id: str) -> Optional[Summary]:
        stmt = select(Summary).where(Summary.id == summary_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

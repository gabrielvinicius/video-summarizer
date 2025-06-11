# src/summarization/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.database import get_db
from src.summarization.application.summarization_service import SummarizationService
from src.summarization.infrastructure.dependencies import get_summarizer
from src.summarization.infrastructure.summary_repository import SummaryRepository
from src.transcription.api.dependencies import get_transcription_service


async def get_summary_service(db: AsyncSession = Depends(get_db),
                              trasncription_service=Depends(get_transcription_service),
                              summarizer=Depends(get_summarizer)
                              ) -> SummarizationService:
    repo = SummaryRepository(db)
    return SummarizationService(summary_repo=repo, trasncription_service=trasncription_service, summarizer=summarizer)

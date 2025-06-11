# src/summarization/application/summarization_service.py
import logging
from src.summarization.domain.summary import Summary, SummaryStatus
from src.summarization.infrastructure.summary_repository import SummaryRepository
from src.summarization.infrastructure.summarizer_interface import ISummarizer
from datetime import datetime

logger = logging.getLogger(__name__)

class SummarizationService:
    def __init__(self, summarizer: ISummarizer, repo: SummaryRepository):
        self.summarizer = summarizer
        self.repo = repo

    async def summarize_transcription(self, transcription_id: str, transcription_text: str) -> Summary:
        summary = Summary(
            transcription_id=transcription_id,
            status=SummaryStatus.PROCESSING
        )
        await self.repo.save(summary)

        try:
            result = await self.summarizer.summarize(transcription_text)
            summary.mark_as_completed(result)
        except Exception as e:
            logger.error(f"Summarization failed: {e}", exc_info=True)
            summary.mark_as_failed(str(e))

        return await self.repo.save(summary)

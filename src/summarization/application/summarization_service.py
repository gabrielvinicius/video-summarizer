# src/summarization/application/summarization_service.py
from src.summarization.domain.summary import Summary, SummaryStatus
from src.summarization.infrastructure.interfaces import ISummarizer
from src.summarization.infrastructure.summary_repository import SummaryRepository
from src.transcription.application.transcription_service import TranscriptionService


class SummarizationService:
    def __init__(self, summarizer: ISummarizer, summary_repo: SummaryRepository,
                 transcription_service: TranscriptionService):

        self.summarizer = summarizer
        self.summary_repo = summary_repo
        self.transcription_service = transcription_service

    async def process_summary(self, transcription_id: str) -> Summary:
        try:
            summary = await self.summary_repo.find_by_transcription_id(transcription_id)
            if summary and summary.status == SummaryStatus.COMPLETED:
                return summary

            if not summary:
                summary = Summary(transcription_id=transcription_id)
                summary.mark_as_processing()
                await self.summary_repo.save(summary)

            transcription = await self.transcription_service.get_transcription_by_id(transcription_id=transcription_id)
            if not transcription or not transcription.text:
                raise ValueError("Transcription not found or has no text")

            text = await self.summarizer.summarize(transcription.text)
            summary.mark_as_completed(text)
            return await self.summary_repo.save(summary)

        except Exception as e:
            if summary:
                summary.mark_as_failed(str(e)[:500])
                await self.summary_repo.save(summary)
            raise

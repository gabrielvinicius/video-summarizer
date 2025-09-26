# src/summarization/application/summarization_service.py
import time

import structlog

from src.analytics.application.analytics_service import AnalyticsService
from src.metrics.application.metrics_service import MetricsService
from src.shared.events.event_bus import EventBus
# Importação dos eventos de domínio tipados
from src.shared.events.domain_events import SummaryRequested, SummarizationProgress
from src.summarization.domain.interfaces import ISummaryRepository
from src.summarization.domain.summary import Summary, SummaryStatus
from src.summarization.infrastructure.interfaces import ISummarizer
from src.transcription.application.transcription_service import TranscriptionService

logger = structlog.get_logger(__name__)


class SummarizationService:
    def __init__(self,
                 summarizer: ISummarizer,
                 summary_repo: ISummaryRepository,
                 transcription_service: TranscriptionService,
                 metrics_service: MetricsService,
                 analytics_service: AnalyticsService,
                 event_bus: EventBus
                 ):
        self.summarizer = summarizer
        self.summary_repo = summary_repo
        self.transcription_service = transcription_service
        self.metrics_service = metrics_service
        self.analytics_service = analytics_service
        self.event_bus = event_bus

    async def request_summary(self, video_id: str, user_id: str, language: str):
        """Dispatches a typed domain event to request a video summary."""
        logger.info("summary.requested", video_id=video_id, user_id=user_id, language=language)
        event = SummaryRequested(
            video_id=video_id,
            user_id=user_id,
            language=language
        )
        await self.event_bus.publish(event)

    async def process_summary(self, transcription_id: str) -> Summary:
        start_time = time.time()
        logger.info("summarization.started", transcription_id=transcription_id)

        summary = await self.summary_repo.find_by_transcription_id(transcription_id)
        if summary and summary.status == SummaryStatus.COMPLETED:
            logger.info("summarization.completed", transcription_id=transcription_id, from_cache=True)
            return summary

        if not summary:
            summary = Summary.create(transcription_id=transcription_id)
            await self.summary_repo.save(summary)

        try:
            transcription = await self.transcription_service.get_transcription_by_id(transcription_id=transcription_id)
            if not transcription or not transcription.text:
                raise ValueError("Transcription not found or has no text")

            text_length = len(transcription.text)
            video_duration_seconds = text_length / 100  # Simulação
            estimate = await self.analytics_service.estimate_processing_time(video_duration_seconds)

            # Publica progresso estimado (25% no início)
            await self.event_bus.publish(SummarizationProgress(
                transcription_id=transcription_id,
                progress=25,
                stage="summarization",
                estimated_total_seconds=estimate["estimated_total_seconds"]
            ))

            text = await self.summarizer.summarize(transcription.text)

            # Publica progresso (75% após sumarização)
            await self.event_bus.publish(SummarizationProgress(
                transcription_id=transcription_id,
                progress=75,
                stage="summarization"
            ))

            summary.mark_as_completed(text)

            self.metrics_service.increment_summarization('success')
            duration = time.time() - start_time
            self.metrics_service.observe_summarization_duration(transcription_id, duration)

            logger.info("summarization.completed", transcription_id=transcription_id, duration=duration)

            return await self.summary_repo.save(summary)

        except Exception as e:
            self.metrics_service.increment_summarization('failure')
            logger.error("summarization.failed", transcription_id=transcription_id, error=str(e))
            if summary:
                summary.mark_as_failed(str(e)[:500])
                await self.summary_repo.save(summary)
            raise

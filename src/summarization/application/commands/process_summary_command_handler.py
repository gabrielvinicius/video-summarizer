# src/summarization/application/commands/process_summary_command_handler.py
import time
import structlog

from src.analytics.application.queries.analytics_queries import AnalyticsQueries
from src.metrics.application.metrics_service import MetricsService
from src.shared.events.domain_events import SummarizationProgress
from src.shared.events.event_bus import EventBus
from src.summarization.domain.interfaces import ISummaryRepository
from src.summarization.domain.summary import Summary, SummaryStatus
from src.summarization.infrastructure.interfaces import ISummarizer
from src.transcription.application.queries.transcription_queries import TranscriptionQueries
from .process_summary_command import ProcessSummaryCommand

logger = structlog.get_logger(__name__)


class ProcessSummaryCommandHandler:
    def __init__(
        self,
        summarizer: ISummarizer,
        summary_repo: ISummaryRepository,
        transcription_queries: TranscriptionQueries,
        metrics_service: MetricsService,
        analytics_queries: AnalyticsQueries, # Correct dependency
        event_bus: EventBus
    ):
        self.summarizer = summarizer
        self.summary_repo = summary_repo
        self.transcription_queries = transcription_queries
        self.metrics_service = metrics_service
        self.analytics_queries = analytics_queries # Correct dependency
        self.event_bus = event_bus

    async def handle(self, command: ProcessSummaryCommand) -> Summary:
        start_time = time.time()
        logger.info("summarization.started", transcription_id=command.transcription_id, provider=command.provider)

        summary = await self.summary_repo.find_by_transcription_id(command.transcription_id)
        if summary and summary.status == SummaryStatus.COMPLETED:
            logger.info("summarization.completed", transcription_id=command.transcription_id, from_cache=True)
            return summary

        if not summary:
            summary = Summary.create(transcription_id=command.transcription_id, provider=command.provider)
        else:
            summary.provider = command.provider
        
        await self.summary_repo.save(summary)

        try:
            transcription = await self.transcription_queries.get_by_id(command.transcription_id)
            if not transcription or not transcription.text:
                raise ValueError("Transcription not found or has no text")

            text_length = len(transcription.text)
            video_duration_seconds = text_length / 100
            estimate = await self.analytics_queries.estimate_processing_time(video_duration_seconds)

            await self.event_bus.publish(SummarizationProgress(
                transcription_id=command.transcription_id,
                progress=25,
                stage="summarization",
                estimated_total_seconds=estimate["estimated_total_seconds"]
            ))

            text = await self.summarizer.summarize(transcription.text)

            await self.event_bus.publish(SummarizationProgress(
                transcription_id=command.transcription_id,
                progress=75,
                stage="summarization"
            ))

            summary.mark_as_completed(text)

            duration = time.time() - start_time
            self.metrics_service.increment_summarization('success')
            self.metrics_service.observe_summarization_duration(
                transcription_id=command.transcription_id, 
                duration=duration, 
                provider=self.summarizer.provider_name
            )

            logger.info("summarization.completed", transcription_id=command.transcription_id, duration=duration)

            return await self.summary_repo.save(summary)

        except Exception as e:
            self.metrics_service.increment_summarization('failure')
            logger.error("summarization.failed", transcription_id=command.transcription_id, error=str(e))
            if summary:
                summary.mark_as_failed(str(e)[:500])
                await self.summary_repo.save(summary)
            raise

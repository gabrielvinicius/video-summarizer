# src/summarization/application/summarization_service.py
import time

import structlog  # Nova importação para logging estruturado

# Importar as métricas do main.py (ou de um módulo centralizado)
from src.metrics.application.metrics_service import MetricsService
from src.summarization.domain.summary import Summary, SummaryStatus
from src.summarization.infrastructure.interfaces import ISummarizer
from src.summarization.infrastructure.summary_repository import SummaryRepository
from src.transcription.application.transcription_service import TranscriptionService
from src.analytics.application.analytics_service import AnalyticsService

# Obtém um logger estruturado
logger = structlog.get_logger(__name__)

class SummarizationService:
    def __init__(self, summarizer: ISummarizer, summary_repo: SummaryRepository,
                 transcription_service: TranscriptionService,
                 metrics_service: MetricsService,
                 analytics_service: AnalyticsService,
                 ):

        self.summarizer = summarizer
        self.summary_repo = summary_repo
        self.transcription_service = transcription_service
        self.metrics_service = metrics_service
        self.analytics_service = analytics_service

    async def process_summary(self, transcription_id: str) -> Summary:
        start_time = time.time()
        logger.info("summarization.started", transcription_id=transcription_id)

        try:
            summary = await self.summary_repo.find_by_transcription_id(transcription_id)
            if summary and summary.status == SummaryStatus.COMPLETED:
                logger.info("summarization.completed", transcription_id=transcription_id, from_cache=True)
                return summary

            if not summary:
                summary = Summary(transcription_id=transcription_id)
                summary.mark_as_processing()
                await self.summary_repo.save(summary)

            transcription = await self.transcription_service.get_transcription_by_id(transcription_id=transcription_id)
            if not transcription or not transcription.text:
                raise ValueError("Transcription not found or has no text")

            # Estimar tempo de processamento (simulado)
            text_length = len(transcription.text)
            video_duration_seconds = text_length / 100  # Simulação grosseira
            estimate = await self.analytics_service.estimate_processing_time(video_duration_seconds)

            # Publica progresso estimado (25% no início)
            await self._publish_event("summarization_progress", {
                "transcription_id": transcription_id,
                "progress": 25,
                "estimated_total_seconds": estimate["estimated_total_seconds"],
                "stage": "summarization"
            })

            text = await self.summarizer.summarize(transcription.text)

            # Publica progresso (75% após sumarização)
            await self._publish_event("summarization_progress", {
                "transcription_id": transcription_id,
                "progress": 75,
                "stage": "summarization"
            })

            summary.mark_as_completed(text)

            # Registrar sucesso e a duração específica deste vídeo (via transcription_id)
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

    async def _publish_event(self, event_name: str, payload: dict):
        """Helper method to publish events."""
        try:
            await self.event_bus.publish(event_name, payload)
        except Exception as e:
            logger.error(f"Failed to publish event {event_name}: {str(e)}", exc_info=True)
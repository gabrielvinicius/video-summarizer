# src/summarization/application/summarization_service.py
import time

import structlog  # Nova importação para logging estruturado

# Importar as métricas do main.py (ou de um módulo centralizado)
from src.metrics.application.metrics_service import MetricsService
from src.summarization.domain.summary import Summary, SummaryStatus
from src.summarization.infrastructure.interfaces import ISummarizer
from src.summarization.infrastructure.summary_repository import SummaryRepository
from src.transcription.application.transcription_service import TranscriptionService

# Obtém um logger estruturado
logger = structlog.get_logger(__name__)

class SummarizationService:
    def __init__(self, summarizer: ISummarizer, summary_repo: SummaryRepository,
                 transcription_service: TranscriptionService,
                 metrics_service: MetricsService, # Nova dependência
                 ):

        self.summarizer = summarizer
        self.summary_repo = summary_repo
        self.transcription_service = transcription_service
        self.metrics_service = metrics_service # Injeta o serviço de métricas

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

            text = await self.summarizer.summarize(transcription.text)
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
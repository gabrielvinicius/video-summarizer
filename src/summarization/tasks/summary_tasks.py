import asyncio
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database import get_db
from src.summarization.application.summarization_service import SummarizationService
from src.summarization.infrastructure.dependencies import create_summarizer_service
from src.summarization.infrastructure.summary_repository import SummaryRepository
from src.transcription.application.transcription_service import TranscriptionService
# Import other necessary dependencies manually for the Celery context
from src.shared.container import ApplicationContainer


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def process_summary_task(self, transcription_id: str, provider: str):
    """
    Celery entrypoint to trigger the summarization pipeline with a specific provider.
    """
    async def run():
        async for db_session in get_db():
            # Manually build the service with the dynamic provider
            container = ApplicationContainer()
            # We need to initialize parts of the container manually to get dependencies
            await container.initialize(db_session)

            summarizer_instance = create_summarizer_service(provider)
            
            summarization_service = SummarizationService(
                summarizer=summarizer_instance,
                summary_repo=container["summary_repository"],
                transcription_service=container["transcription_service"],
                metrics_service=container["metrics_service"],
                analytics_service=container["analytics_service"],
                event_bus=container["event_bus"]
            )
            
            await summarization_service.process_summary(transcription_id, provider=provider)

    asyncio.run(run())

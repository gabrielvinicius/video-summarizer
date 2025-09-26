import asyncio
from celery import shared_task

from src.shared.infrastructure.database import get_db
# Import the new CQRS components
from src.summarization.application.commands.process_summary_command import ProcessSummaryCommand
from src.summarization.application.commands.process_summary_command_handler import ProcessSummaryCommandHandler
from src.summarization.infrastructure.dependencies import create_summarizer_service
# Import the container to help build dependencies
from src.shared.container import ApplicationContainer


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def process_summary_task(self, transcription_id: str, provider: str):
    """
    Celery entrypoint to trigger the summarization pipeline with a specific provider.
    """
    async def run():
        async for db_session in get_db():
            # Manually build dependencies required for the handler
            container = ApplicationContainer()
            await container.initialize(db_session)

            # 1. Create the specific summarizer instance using the factory
            summarizer_instance = create_summarizer_service(provider)
            
            # 2. Create the command handler with all its dependencies
            handler = ProcessSummaryCommandHandler(
                summarizer=summarizer_instance,
                summary_repo=container["summary_repository"],
                transcription_service=container["transcription_service"],
                metrics_service=container["metrics_service"],
                analytics_service=container["analytics_service"],
                event_bus=container["event_bus"]
            )
            
            # 3. Create the command object
            command = ProcessSummaryCommand(
                transcription_id=transcription_id,
                provider=provider
            )

            # 4. Execute the handler
            await handler.handle(command)

    asyncio.run(run())

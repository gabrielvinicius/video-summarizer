# src/summarization/tasks/tasks.py

from celery import shared_task
import asyncio
from src.shared.container import build_container
from src.shared.infrastructure.database import create_async_session

@shared_task
def process_summary_task(transcription_id: str):
    """
    Celery entrypoint to trigger summarization pipeline for a transcription.
    """
    async def run():
        async with create_async_session() as session:
            container = build_container(session)
            summarization_service = container["summarization_service"]
            await summarization_service.process_summary(transcription_id)

    asyncio.run(run())

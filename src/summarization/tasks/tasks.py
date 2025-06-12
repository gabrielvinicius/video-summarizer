# src/summarization/tasks/tasks.py

from celery import shared_task
import asyncio
from src.shared.container import build_container
from src.shared.infrastructure.database import AsyncSessionLocal

@shared_task
def process_summary_task(transcription_id: str):
    """
    Celery entrypoint to trigger summarization pipeline for a transcription.
    """
    async def run():
        async with AsyncSessionLocal() as session:
            container = build_container(session)
            summarization_service = await container["summarization_service"]
            await summarization_service.process_summary(transcription_id)

    asyncio.run(run())

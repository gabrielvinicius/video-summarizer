# src/summarization/application/event_handlers.py
import logging
from typing import Dict, Any

from src.shared.events.domain_events import SummarizationRequested
from src.shared.events.event_bus import EventBus
from src.summarization.tasks.summary_tasks import process_summary_task

logger = logging.getLogger(__name__)


async def register_event_handlers(event_bus: EventBus):
    """Registers all summarization-related event handlers."""

    async def handle_summarization_requested(event_data: Dict[str, Any]):
        """Handles SummarizationRequested events by triggering the summarization task."""
        try:
            transcription_id = event_data["transcription_id"]
            provider = event_data.get("provider", "huggingface")  # Default provider
            logger.info(f"Received SummarizationRequested for {transcription_id} with provider {provider}")

            # Dispatch summarization task with the chosen provider
            process_summary_task.delay(transcription_id=transcription_id, provider=provider)
            logger.info(f"Summary task dispatched for transcription {transcription_id}")

        except KeyError as e:
            logger.error(f"Missing key in SummarizationRequested event: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to handle SummarizationRequested event: {str(e)}", exc_info=True)

    event_bus.subscribe(SummarizationRequested, handle_summarization_requested)
    logger.info("Successfully registered SummarizationRequested handler.")

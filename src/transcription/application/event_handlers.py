# src/transcription/application/event_handlers.py
import logging
from typing import Dict, Any

from src.shared.events.domain_events import TranscriptionRequested
from src.shared.events.event_bus import EventBus
from src.transcription.tasks.tasks import process_transcription_task

logger = logging.getLogger(__name__)


async def register_event_handlers(event_bus: EventBus) -> None:
    """Registers all transcription-related event handlers with the event bus."""

    async def handle_transcription_requested(event_data: Dict[str, Any]) -> None:
        """Handles TranscriptionRequested events by triggering the transcription task."""
        try:
            video_id = event_data["video_id"]
            provider = event_data.get("provider", "whisper")  # Default to whisper if not provided
            logger.info(f"Received TranscriptionRequested event for video {video_id} with provider {provider}")

            # Dispatch transcription task with the chosen provider
            process_transcription_task.delay(video_id=video_id, provider=provider)
            logger.info(f"Successfully dispatched transcription task for video {video_id}")

        except KeyError as e:
            logger.error(f"Missing required field in TranscriptionRequested event data: {e}")
        except Exception as e:
            logger.error(f"Failed to handle TranscriptionRequested event: {e}", exc_info=True)

    try:
        event_bus.subscribe(TranscriptionRequested, handle_transcription_requested)
        logger.info("Successfully registered TranscriptionRequested handler")

    except Exception as e:
        logger.error(f"Failed to register event handlers: {e}", exc_info=True)
        raise

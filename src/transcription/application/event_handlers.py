""" Event handlers for transcription-related events.
This module registers handlers for events related to video uploads and transcription processing.
"""
# src/transcription/application/event_handlers.py
import logging
from typing import Dict, Any
from src.shared.events.event_bus import EventBus
from src.transcription.tasks.tasks import process_transcription_task

logger = logging.getLogger(__name__)


async def register_event_handlers(event_bus: EventBus) -> None:
    """
    Registers all transcription-related event handlers with the event bus.
    """

    async def handle_video_uploaded(event_data: Dict[str, Any]) -> None:
        """
        Handles video_uploaded events by triggering transcription processing.

        Args:
            event_data: Dictionary containing event data with keys:
                      - video_id: UUID of the uploaded video
                      - file_path: Path to the video file (optional)
                      - user_id: ID of the uploading user (optional)
        """
        try:
            video_id = event_data["video_id"]
            logger.info(f"Received video_uploaded event for video {video_id}")

            if not video_id:
                raise ValueError("Missing required video_id in event data")

            # Dispatch transcription task asynchronously (via Celery)
            process_transcription_task.delay(video_id)
            logger.info(f"Successfully dispatched transcription task for video {video_id}")

        except KeyError as e:
            logger.error(f"Missing required field in event data: {e}")
        except Exception as e:
            logger.error(f"Failed to handle video_uploaded event: {e}", exc_info=True)

    try:
        event_bus.subscribe("video_uploaded", handle_video_uploaded)
        logger.info("Successfully registered video_uploaded handler")
    except Exception as e:
        logger.error(f"Failed to register event handlers: {e}", exc_info=True)
        raise

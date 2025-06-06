import logging
from typing import Dict, Any
from src.shared.events.event_bus import EventBus
from src.transcription.tasks.tasks import process_transcription_task

logger = logging.getLogger(__name__)


async def register_event_handlers(event_bus: EventBus) -> None:
    """
    Registers all transcription-related event handlers with the event bus.

    Args:
        event_bus: The event bus instance to register handlers with
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

            # Async task dispatch (Celery .delay é sync, mas o handler pode ser async)
            process_transcription_task.delay(video_id)
            logger.info(f"Successfully dispatched transcription task for video {video_id}")

        except KeyError as e:
            logger.error(f"Missing required field in event data: {e}")
        except Exception as e:
            logger.error(f"Failed to handle video_uploaded event: {e}", exc_info=True)
            # Consider adding retry logic or dead-letter queue handling here

    try:
        # Suporte tanto para handlers sync quanto async
        event_bus.subscribe("video_uploaded", handle_video_uploaded)
        logger.info("Successfully registered video_uploaded handler")
    except Exception as e:
        logger.error(f"Failed to register event handlers: {e}", exc_info=True)
        raise

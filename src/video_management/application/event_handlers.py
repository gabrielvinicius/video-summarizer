import logging
from typing import Dict, Any
from src.video_management.application.video_service import VideoService
from src.video_management.domain.video import VideoStatus

logger = logging.getLogger(__name__)


async def register_video_event_handlers(event_bus, video_service: VideoService):
    """
    Register event handlers for reacting to transcription events.
    """

    async def handle_transcription_started(event_data: Dict[str, Any]):
        try:
            video_id = event_data["video_id"]
            logger.info(f"Transcription started for video {video_id}")
            await video_service.update_video_status(video_id, VideoStatus.PROCESSING)
        except Exception as e:
            logger.error(f"Failed to handle transcription_started: {e}", exc_info=True)

    async def handle_transcription_completed(event_data: Dict[str, Any]):
        try:
            video_id = event_data["video_id"]
            logger.info(f"Transcription completed for video {video_id}")
            await video_service.update_video_status(video_id, VideoStatus.COMPLETED)
        except Exception as e:
            logger.error(f"Failed to handle transcription_completed: {e}", exc_info=True)

    async def handle_transcription_failed(event_data: Dict[str, Any]):
        try:
            video_id = event_data["video_id"]
            logger.warning(f"Transcription failed for video {video_id}")
            await video_service.update_video_status(video_id, VideoStatus.FAILED)
        except Exception as e:
            logger.error(f"Failed to handle transcription_failed: {e}", exc_info=True)

    try:
        event_bus.subscribe("transcription_started", handle_transcription_started)
        event_bus.subscribe("transcription_completed", handle_transcription_completed)
        event_bus.subscribe("transcription_failed", handle_transcription_failed)

        logger.info("Successfully registered transcription lifecycle handlers")
    except Exception as e:
        logger.error(f"Failed to register video event handlers: {e}", exc_info=True)
        raise

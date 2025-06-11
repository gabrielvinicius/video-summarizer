# src/summarization/application/event_handlers.py

import logging
from typing import Dict, Any
from src.shared.events.event_bus import EventBus
from src.summarization.tasks.tasks import process_summary_task

logger = logging.getLogger(__name__)

def register_event_handlers(event_bus: EventBus, summarization_service, transcription_repo):
    async def handle_transcription_completed(event_data: Dict[str, Any]):
        try:
            transcription_id = event_data["transcription_id"]
            logger.info(f"Received transcription_completed for {transcription_id}")

            # Pode fazer verificação básica se quiser
            process_summary_task.delay(transcription_id)
            logger.info(f"Summary task dispatched for transcription {transcription_id}")

        except KeyError as e:
            logger.error(f"Missing key in event: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to handle event: {str(e)}", exc_info=True)

    event_bus.subscribe("transcription_completed", handle_transcription_completed)

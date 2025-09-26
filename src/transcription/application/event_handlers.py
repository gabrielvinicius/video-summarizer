""" Event handlers for transcription-related events.
This module registers handlers for events related to video uploads and transcription processing.
"""
# src/transcription/application/event_handlers.py
import logging
from typing import Dict, Any

# Importação dos eventos de domínio tipados
from src.shared.events.domain_events import SummaryRequested, VideoUploaded
from src.shared.events.event_bus import EventBus
from src.transcription.tasks.tasks import process_transcription_task

logger = logging.getLogger(__name__)


async def register_event_handlers(event_bus: EventBus) -> None:
    """
    Registers all transcription-related event handlers with the event bus.
    """

    async def handle_video_uploaded(event_data: Dict[str, Any]) -> None:
        """Handles VideoUploaded events by triggering transcription processing."""
        try:
            video_id = event_data["video_id"]
            logger.info(f"Received VideoUploaded event for video {video_id}")
            # A task de transcrição é despachada sem linguagem, usando o padrão.
            process_transcription_task.delay(video_id=video_id)
            logger.info(f"Successfully dispatched transcription task for video {video_id}")
        except KeyError as e:
            logger.error(f"Missing required field in VideoUploaded event data: {e}")
        except Exception as e:
            logger.error(f"Failed to handle VideoUploaded event: {e}", exc_info=True)

    async def handle_summary_requested(event_data: Dict[str, Any]) -> None:
        """
        Handles SummaryRequested events by triggering transcription processing.
        """
        try:
            video_id = event_data["video_id"]
            language = event_data.get("language", "en") # Pega a linguagem do evento
            logger.info(f"Received SummaryRequested event for video {video_id}")

            # Despacha a tarefa de transcrição com a linguagem especificada.
            process_transcription_task.delay(video_id=video_id, language=language)
            logger.info(f"Dispatched transcription task for {video_id} with language '{language}'.")

        except KeyError as e:
            logger.error(f"Missing required field in SummaryRequested event data: {e}")
        except Exception as e:
            logger.error(f"Failed to handle SummaryRequested event: {e}", exc_info=True)

    try:
        # Assinatura atualizada para usar o evento de domínio tipado
        event_bus.subscribe(VideoUploaded, handle_video_uploaded)
        logger.info("Successfully registered VideoUploaded handler")

        # Assinatura para o evento de solicitação de resumo
        event_bus.subscribe(SummaryRequested, handle_summary_requested)
        logger.info("Successfully registered SummaryRequested handler")

    except Exception as e:
        logger.error(f"Failed to register event handlers: {e}", exc_info=True)
        raise

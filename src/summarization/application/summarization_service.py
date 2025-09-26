# src/summarization/application/summarization_service.py
import structlog

from src.shared.events.domain_events import SummarizationRequested
from src.shared.events.event_bus import EventBus

logger = structlog.get_logger(__name__)


class SummarizationService:
    """Facade service to dispatch summarization commands."""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def request_summary(self, transcription_id: str, provider: str):
        """Dispatches a SummarizationRequested event to the event bus."""
        logger.info("summary.requested", transcription_id=transcription_id, provider=provider)
        event = SummarizationRequested(
            transcription_id=transcription_id,
            provider=provider
        )
        await self.event_bus.publish(event)

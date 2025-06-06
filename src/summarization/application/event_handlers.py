# summarization/application/event_handlers.py
from src.shared.events.event_bus import EventBus
from ..tasks.summary_tasks import generate_summary_task


async def register_event_handlers(event_bus: EventBus):
    async def handle_transcription_completed(event_data: dict):
        transcription_id = event_data["transcription_id"]
        generate_summary_task.delay(transcription_id)

    event_bus.subscribe("transcription_completed", handle_transcription_completed)

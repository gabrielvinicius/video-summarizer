# transcription/application/event_handlers.py
from src.shared.events.event_bus import EventBus
from ..tasks.tasks import process_transcription_task


def register_event_handlers(event_bus: EventBus):
    async def handle_video_uploaded(event_data: dict):
        video_id = event_data["video_id"]
        file_path = event_data["file_path"]
        process_transcription_task.delay(video_id, file_path)

    event_bus.subscribe("video_uploaded", handle_video_uploaded)

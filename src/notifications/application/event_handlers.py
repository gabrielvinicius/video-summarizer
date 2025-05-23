# notifications/application/event_handlers.py
from src.shared.events.event_bus import EventBus


def register_event_handlers(event_bus: EventBus):
    async def handle_summary_generated(event_data: dict):
        user_id = event_data["user_id"]
        video_id = event_data["video_id"]
        message = f"Seu resumo para o vídeo {video_id} está pronto!"
        send_notification_task.delay(user_id, message, "EMAIL")

    event_bus.subscribe("summary_generated", handle_summary_generated)

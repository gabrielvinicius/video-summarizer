from celery import shared_task
from src.notifications.application.notification_service import NotificationService
from src.shared.events.event_bus import get_event_bus


@shared_task
def send_notification_task(user_id: str, message: str, notification_type):
    service = NotificationService(
        email_adapter=...,
        sms_adapter=...,
        webhook_adapter=...,
        notification_repository=...,
        user_repository=...
    )
    return service.send_notification(user_id, message, notification_type)

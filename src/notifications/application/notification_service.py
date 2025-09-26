# src/notifications/application/notification_service.py
from src.notifications.domain.notification import Notification, NotificationType
# Import the new CQRS components
from .commands.send_notification_command import SendNotificationCommand
from .commands.send_notification_command_handler import SendNotificationCommandHandler


class NotificationService:
    """Facade service to dispatch notification commands."""
    def __init__(
        self,
        send_notification_handler: SendNotificationCommandHandler,
    ):
        self.send_notification_handler = send_notification_handler

    async def send_notification(
        self, 
        user_id: str, 
        message: str, 
        notification_type: NotificationType
    ) -> Notification:
        """Dispatches the SendNotificationCommand."""
        command = SendNotificationCommand(
            user_id=user_id,
            message=message,
            notification_type=notification_type
        )
        return await self.send_notification_handler.handle(command)

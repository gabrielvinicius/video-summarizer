# src/notifications/application/commands/send_notification_command_handler.py
import structlog

from src.auth.infrastructure.user_repository import UserRepository
from src.notifications.domain.notification import Notification, NotificationType
from src.notifications.infrastructure.notification_repository import NotificationRepository
from src.shared.utils.id_generator import generate_id
from .send_notification_command import SendNotificationCommand

logger = structlog.get_logger(__name__)


class SendNotificationCommandHandler:
    def __init__(
        self,
        email_adapter,
        sms_adapter,
        webhook_adapter,
        notification_repository: NotificationRepository,
        user_repository: UserRepository,
    ):
        self.email_adapter = email_adapter
        self.sms_adapter = sms_adapter
        self.webhook_adapter = webhook_adapter
        self.notification_repo = notification_repository
        self.user_repo = user_repository

    async def handle(self, command: SendNotificationCommand) -> Notification:
        """Handles the notification sending process."""
        user = await self.user_repo.find_by_id(command.user_id)
        if not user:
            raise ValueError("User not found")

        notification = Notification(
            id=generate_id(),
            user_id=command.user_id,
            type=command.notification_type,
            content=command.message
        )
        await self.notification_repo.save(notification)

        try:
            if command.notification_type == NotificationType.EMAIL:
                await self.email_adapter.send(user.email, "Notification", command.message)
            elif command.notification_type == NotificationType.SMS:
                await self.sms_adapter.send(user.phone, command.message)
            elif command.notification_type == NotificationType.WEBHOOK:
                await self.webhook_adapter.send(user.webhook_url, {"message": command.message})

            notification.mark_as_sent()
            logger.info("notification.sent", notification_id=str(notification.id), type=command.notification_type)
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error("notification.failed", notification_id=str(notification.id), error=str(e))

        await self.notification_repo.save(notification)
        return notification

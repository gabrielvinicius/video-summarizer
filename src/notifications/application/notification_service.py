from typing import Optional
from src.notifications.domain.notification import Notification, NotificationStatus, NotificationType
from src.shared.utils.id_generator import generate_id


class NotificationService:
    def __init__(
        self,
        email_adapter,  # Adaptador para SMTP
        sms_adapter,  # Adaptador para Twilio
        webhook_adapter,  # Adaptador para webhook
        notification_repository,
        user_repository  # Repositório do módulo auth
    ):
        self.email_adapter = email_adapter
        self.sms_adapter = sms_adapter
        self.webhook_adapter = webhook_adapter
        self.notification_repo = notification_repository
        self.user_repo = user_repository

    async def send_notification(
        self,
        user_id: str,
        message: str,
        notification_type: NotificationType
    ) -> Notification:
        """Envia uma notificação e persiste o status."""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")

        notification = Notification(
            id=generate_id(),
            user_id=user_id,
            type=notification_type,
            content=message
        )
        await self.notification_repo.save(notification)

        try:
            if notification_type == NotificationType.EMAIL:
                await self.email_adapter.send(user.email, message)
            elif notification_type == NotificationType.SMS:
                await self.sms_adapter.send(user.phone, message)
            elif notification_type == NotificationType.WEBHOOK:
                await self.webhook_adapter.send(user.webhook_url, message)

            notification.mark_as_sent()
        except Exception as e:
            notification.mark_as_failed(str(e))

        await self.notification_repo.save(notification)
        return notification

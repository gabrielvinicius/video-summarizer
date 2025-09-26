# src/notifications/bootstrap.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.auth.infrastructure.user_repository import UserRepository
from src.notifications.application.commands.send_notification_command_handler import SendNotificationCommandHandler
from src.notifications.application.notification_service import NotificationService
from src.notifications.application.queries.notification_queries import NotificationQueries
from src.notifications.config.settings import SmtpSettings
from src.notifications.infrastructure.notification_repository import NotificationRepository
from src.notifications.infrastructure.smtp_adapter import SMTPAdapter
from src.notifications.infrastructure.sms_adapter import SmsAdapter
from src.notifications.infrastructure.webhook_adapter import WebhookAdapter

def bootstrap_notification_module(
    db_session: AsyncSession,
    user_repository: UserRepository, # Cross-context dependency
) -> Dict[str, Any]:
    """Constructs and returns the services for the notification module."""
    smtp_settings = SmtpSettings()
    email_adapter = SMTPAdapter(
        host=smtp_settings.smtp_host,
        port=smtp_settings.smtp_port,
        username=smtp_settings.smtp_user,
        password=smtp_settings.smtp_password
    )
    sms_adapter = SmsAdapter()
    webhook_adapter = WebhookAdapter()
    notification_repository = NotificationRepository(db=db_session)

    send_notification_handler = SendNotificationCommandHandler(
        email_adapter=email_adapter,
        sms_adapter=sms_adapter,
        webhook_adapter=webhook_adapter,
        notification_repository=notification_repository,
        user_repository=user_repository
    )

    notification_service = NotificationService(send_notification_handler=send_notification_handler)
    notification_queries = NotificationQueries(notification_repository=notification_repository)

    return {
        "notification_repository": notification_repository,
        "notification_service": notification_service,
        "notification_queries": notification_queries,
    }

# src/notifications/application/queries/notification_queries.py
from typing import Optional, List
from uuid import UUID

from src.notifications.domain.notification import Notification
from src.notifications.infrastructure.notification_repository import NotificationRepository


class NotificationQueries:
    """Handles all read-only operations for notifications."""
    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository

    async def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """Retrieves a notification by its unique ID."""
        return await self.notification_repository.find_by_id(notification_id)

    async def list_by_user(self, user_id: str) -> List[Notification]:
        """Lists all notifications for a specific user."""
        return await self.notification_repository.list_by_user(user_id)

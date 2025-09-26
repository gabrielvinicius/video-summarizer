from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.notifications.domain.notification import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, notification_id: str) -> Optional[Notification]:
        """Finds a notification by its ID."""
        result = await self.db.execute(
            select(Notification).where(Notification.id == UUID(notification_id))
        )
        return result.scalar_one_or_none()

    async def save(self, notification: Notification) -> Notification:
        """Saves a notification to the database."""
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def list_by_user(self, user_id: str) -> List[Notification]:
        """Lists all notifications for a specific user."""
        result = await self.db.execute(
            select(Notification).where(Notification.user_id == UUID(user_id))
        )
        return result.scalars().all()

    async def mark_as_read(self, notification_id: str) -> bool:
        """Marks a notification as read."""
        stmt = (
            update(Notification)
            .where(Notification.id == UUID(notification_id))
            .values(read=True)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def delete(self, notification_id: str) -> bool:
        """Deletes a notification by its ID."""
        notification = await self.find_by_id(notification_id)
        if notification:
            await self.db.delete(notification)
            await self.db.commit()
            return True
        return False

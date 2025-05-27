from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from src.notifications.domain.notification import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def find_by_id(self, notification_id: str) -> Notification | None:
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def save(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_by_user(self, user_id: str) -> list[Notification]:
        return self.db.query(Notification).filter(Notification.user_id == user_id).all()

    def mark_as_read(self, notification_id: str) -> bool:
        notification = self.find_by_id(notification_id)
        if notification:
            notification.read = True
            self.db.commit()
            return True
        return False

    def delete(self, notification_id: str) -> bool:
        notification = self.find_by_id(notification_id)
        if notification:
            self.db.delete(notification)
            self.db.commit()
            return True
        return False

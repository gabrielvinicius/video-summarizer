import uuid
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationType(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WEBHOOK = "WEBHOOK"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Notification(BaseModel):
    id: str = uuid.uuid4()
    user_id: int  # ID do usuário (auth module)
    type: NotificationType
    content: str  # Corpo da mensagem
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = datetime.utcnow()
    sent_at: Optional[datetime] = None
    retries: int = 0
    error_message: Optional[str] = None

    def mark_as_sent(self):
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.utcnow()

    def mark_as_failed(self, error: str):
        self.status = NotificationStatus.FAILED
        self.error_message = error
        self.retries += 1

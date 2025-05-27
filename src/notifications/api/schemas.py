from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WEBHOOK = "WEBHOOK"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationBase(BaseModel):
    type: NotificationType
    content: str


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: UUID
    user_id: int
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime]
    retries: int
    error_message: Optional[str]

    class Config:
        from_attributes = True  # Para funcionar com ORM

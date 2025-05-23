from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    type: str
    status: str
    content: str
    sent_at: Optional[datetime] = None

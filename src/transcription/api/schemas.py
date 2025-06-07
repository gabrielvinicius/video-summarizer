from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

class TranscriptionStatus(str, Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TranscriptionBase(BaseModel):
    video_id: UUID
    text: Optional[str] = None

class TranscriptionCreate(TranscriptionBase):
    pass

class TranscriptionRead(TranscriptionBase):
    id: UUID
    status: TranscriptionStatus
    created_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True  # Use orm_mode = True para Pydantic v1

class TranscriptionResponse(TranscriptionRead):
    pass
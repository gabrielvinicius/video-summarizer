import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from datetime import datetime


class TranscriptionStatus(str, Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Transcription(BaseModel):
    id: str = uuid.uuid4()  # UUID
    video_id: str  # ID do vídeo relacionado
    text: str  # Texto transcrito
    status: TranscriptionStatus = TranscriptionStatus.PROCESSING
    created_at: datetime = datetime.utcnow()
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {
        "from_attributes": True  # ✅ novo
    }

    def mark_as_completed(self, text: str):
        self.text = text
        self.status = TranscriptionStatus.COMPLETED
        self.processed_at = datetime.utcnow()

    def mark_as_failed(self, error: str):
        self.status = TranscriptionStatus.FAILED
        self.error_message = error
        self.processed_at = datetime.utcnow()

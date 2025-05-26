import uuid
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SummaryStatus(str, Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Summary(BaseModel):
    id: str =  uuid.uuid4()   # UUID
    transcription_id: str  # ID da transcrição relacionada
    video_id: str  # ID do vídeo relacionado
    content: str  # Texto do resumo
    status: SummaryStatus = SummaryStatus.PROCESSING
    created_at: datetime = datetime.utcnow()
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def mark_as_completed(self, content: str):
        self.content = content
        self.status = SummaryStatus.COMPLETED
        self.processed_at = datetime.utcnow()

    def mark_as_failed(self, error: str):
        self.status = SummaryStatus.FAILED
        self.error_message = error
        self.processed_at = datetime.utcnow()

from sqlalchemy import Column, String, DateTime, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from src.shared.infrastructure.database import Base
from datetime import datetime
import enum
import uuid

#from src.summarization.domain.summary import Summary
#from src.video_management.domain.video import Video


class TranscriptionStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False,unique=True)
    video: Mapped["Video"] = relationship(back_populates="transcription")
    text = Column(String, nullable=True)
    status = Column(SqlEnum(TranscriptionStatus), default=TranscriptionStatus.PROCESSING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    summary: Mapped["Summary"] = relationship(back_populates="transcription")

    def mark_as_completed(self, text: str):
        self.text = text
        self.status = TranscriptionStatus.COMPLETED
        self.processed_at = datetime.utcnow()

    def mark_as_failed(self, error: str):
        self.status = TranscriptionStatus.FAILED
        self.error_message = error
        self.processed_at = datetime.utcnow()

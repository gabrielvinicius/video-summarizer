from sqlalchemy import Column, String, DateTime, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from src.shared.infrastructure.database import Base
from datetime import datetime
import enum
import uuid

from src.transcription.domain.transcription import Transcription


class SummaryStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcription_id = Column(UUID(as_uuid=True), ForeignKey("transcriptions.id"), nullable=False, unique=True)
    transcription: Mapped["Transcription"] = relationship(back_populates="summary")
    #video_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(String, nullable=True)
    status = Column(SqlEnum(SummaryStatus), default=SummaryStatus.PROCESSING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    def mark_as_completed(self, content: str):
        self.content = content
        self.status = SummaryStatus.COMPLETED
        self.processed_at = datetime.utcnow()

    def mark_as_failed(self, error: str):
        self.status = SummaryStatus.FAILED
        self.error_message = error
        self.processed_at = datetime.utcnow()

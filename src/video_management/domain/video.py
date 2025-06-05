import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Enum as SqlEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import Mapped, relationship

#from src.auth.domain.user import User
from src.shared.infrastructure.database import Base
#from src.transcription.domain.transcription import Transcription


class VideoStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # user: Mapped["User"] = relationship(back_populates="videos")
    file_path = Column(String, nullable=False)
    status = Column(SqlEnum(VideoStatus), default=VideoStatus.UPLOADED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    #transcription: Mapped["Transcription"] = relationship(back_populates="video")
    #transcription_id = Column(UUID(as_uuid=True), ForeignKey("transcriptions.id"), nullable=True)
    #summary_id = Column(UUID(as_uuid=True),ForeignKey("summaries.id"), nullable=True)

    def mark_as_processing(self):
        self.status = VideoStatus.PROCESSING

    def mark_as_completed(self):
        self.status = VideoStatus.COMPLETED

    def mark_as_failed(self):
        self.status = VideoStatus.FAILED

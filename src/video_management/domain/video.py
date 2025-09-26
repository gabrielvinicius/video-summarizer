import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Enum as SqlEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from src.shared.infrastructure.database import Base


class VideoStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(SqlEnum(VideoStatus), default=VideoStatus.UPLOADED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    storage_provider = Column(String, nullable=False)  # Added storage provider field

    def mark_as_processing(self):
        self.status = VideoStatus.PROCESSING

    def mark_as_completed(self):
        self.status = VideoStatus.COMPLETED

    def mark_as_failed(self):
        self.status = VideoStatus.FAILED

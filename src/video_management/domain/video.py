from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class VideoStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Video(BaseModel):
    id: str  # UUID
    user_id: str  # ID do usuário (relacionamento com auth module)
    file_path: str  # Caminho no storage (ex: "videos/{user_id}/{video_id}.mp4")
    status: VideoStatus = VideoStatus.UPLOADED
    created_at: datetime = datetime.utcnow()
    transcription_id: Optional[str] = None  # Relacionamento com transcription module
    summary_id: Optional[str] = None  # Relacionamento com summarization module

    def mark_as_processing(self):
        self.status = VideoStatus.PROCESSING

    def mark_as_completed(self):
        self.status = VideoStatus.COMPLETED

    def mark_as_failed(self):
        self.status = VideoStatus.FAILED

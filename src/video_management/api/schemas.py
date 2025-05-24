from typing import Optional

from pydantic import BaseModel
from datetime import datetime


class VideoUploadRequest(BaseModel):
    filename: str


class VideoResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    download_url: Optional[str] = None


class VideoDetailResponse(VideoResponse):
    transcription: Optional[str] = None
    summary: Optional[str] = None

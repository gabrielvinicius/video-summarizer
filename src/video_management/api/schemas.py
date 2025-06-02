from typing import Optional

from pydantic import BaseModel
from datetime import datetime


class VideoUploadRequest(BaseModel):
    filename: str


class VideoResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    download_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class VideoDetailResponse(VideoResponse):
    transcription: Optional[str] = None
    summary: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

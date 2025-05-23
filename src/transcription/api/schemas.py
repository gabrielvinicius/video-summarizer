from typing import Optional

from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    id: str
    video_id: str
    status: str
    text: Optional[str] = None
    error_message: Optional[str] = None

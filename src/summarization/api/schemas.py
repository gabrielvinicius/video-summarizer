from typing import Optional

from pydantic import BaseModel

class SummaryResponse(BaseModel):
    id: str
    video_id: str
    status: str
    content: Optional[str] = None
    error_message: Optional[str] = None
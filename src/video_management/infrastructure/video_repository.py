from sqlalchemy.orm import Session
from src.video_management.domain.video import Video,VideoStatus
from typing import Optional


class VideoRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, video: Video) -> Video:
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video

    def find_by_id(self, video_id: str) -> Optional[Video]:
        return self.db.query(Video).filter(Video.id == video_id).first()

    def update_status(self, video_id: str, status: VideoStatus):
        video = self.find_by_id(video_id)
        if video:
            video.status = status
            self.db.commit()

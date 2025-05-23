from typing import Generator
from sqlalchemy.orm import Session
from src.shared.infrastructure.database import SessionLocal
from src.auth.infrastructure.user_repository import UserRepository
from src.video_management.infrastructure.video_repository import VideoRepository
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.summarization.infrastructure.summary_repository import SummaryRepository
from src.notifications.infrastructure.notification_repository import NotificationRepository

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_video_repository(db: Session = Depends(get_db)) -> VideoRepository:
    return VideoRepository(db)

def get_transcription_repository(db: Session = Depends(get_db)) -> TranscriptionRepository:
    return TranscriptionRepository(db)

def get_summary_repository(db: Session = Depends(get_db)) -> SummaryRepository:
    return SummaryRepository(db)

def get_notification_repository(db: Session = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)
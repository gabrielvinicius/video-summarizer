# src/transcription/api/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from src.shared.infrastructure.database import get_db
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.shared.events.event_bus import get_event_bus
from src.shared.dependencies import get_transcription_repository,get_video_repository,get_db

def get_transcription_service(db: Session = Depends(get_db)) -> TranscriptionService:
    repo = TranscriptionRepository(db)
    return TranscriptionService(event_bus=get_event_bus(),transcription_repository=get_transcription_repository(),video_repository=get_video_repository(),storage_service=)

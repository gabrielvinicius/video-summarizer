# src/video_management/api/dependencies.py

from fastapi import Depends
from src.video_management.application.video_service import VideoService
from src.storage.infrastructure.local_storage_adapter import LocalStorageAdapter
from src.shared.events.event_bus import get_event_bus
from src.shared.infrastructure.database import get_db
from src.video_management.infrastructure.video_repository import VideoRepository
from sqlalchemy.orm import Session


def get_video_service(db: Session = Depends(get_db)) -> VideoService:
    video_repo = VideoRepository(db)
    storage_service = LocalStorageAdapter()  # ou injete config via Depends se necessário
    return VideoService(video_repository=video_repo, storage_service=storage_service,event_bus=get_event_bus())

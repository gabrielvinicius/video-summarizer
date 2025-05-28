# src/video_management/api/dependencies.py

from fastapi import Depends
from src.video_management.application.video_service import VideoService
from src.storage.infrastructure.dependencies import get_storage_service
from src.shared.events.event_bus import get_event_bus
from src.shared.dependencies import get_video_repository


def get_video_service() -> VideoService:
    video_repo = get_video_repository()
    storage_service = get_storage_service()  # ou injete config via Depends se necessário
    return VideoService(video_repository=video_repo, storage_service=storage_service,event_bus=get_event_bus())

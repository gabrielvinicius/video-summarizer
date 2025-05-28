# src/video_management/api/dependencies.py
from fastapi import Depends

from src.shared.events.event_bus import get_event_bus
from src.storage.infrastructure.dependencies import get_storage_service
from src.video_management.application.video_service import VideoService
from src.shared.dependencies import get_video_repository
from src.video_management.infrastructure.video_repository import VideoRepository


async def get_video_service(
    video_repository: VideoRepository = Depends(get_video_repository),
    storage_service=Depends(get_storage_service),
    event_bus=Depends(get_event_bus)
) -> VideoService:
    return VideoService(storage_service, event_bus, video_repository)

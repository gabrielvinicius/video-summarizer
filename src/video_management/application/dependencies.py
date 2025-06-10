from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.events.event_bus import get_event_bus
from src.storage.infrastructure.dependencies import get_storage_service
from src.video_management.application.video_service import VideoService
from src.video_management.infrastructure.dependencies import get_video_repository
from src.video_management.infrastructure.video_repository import VideoRepository


async def get_video_service(db: AsyncSession) -> VideoService:

    video_repository = await get_video_repository(db)
    storage_service = await get_storage_service()
    event_bus = get_event_bus()
    return VideoService(storage_service, event_bus, video_repository)

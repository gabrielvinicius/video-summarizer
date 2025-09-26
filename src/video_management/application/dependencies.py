from sqlalchemy.ext.asyncio import AsyncSession

from src.metrics.application.metrics_service import MetricsService
from src.shared.events.event_bus import EventBus
from src.storage.infrastructure.dependencies import StorageServiceFactory
from src.video_management.application.video_service import VideoService
from src.video_management.infrastructure.video_repository import VideoRepository


async def get_video_service(
    db: AsyncSession, 
    storage_service_factory: StorageServiceFactory, 
    event_bus: EventBus, 
    video_repository: VideoRepository,
    metrics_service: MetricsService
) -> VideoService:
    """Factory function for the VideoService."""
    return VideoService(
        storage_service_factory=storage_service_factory, 
        event_bus=event_bus, 
        video_repository=video_repository,
        metrics_service=metrics_service
    )

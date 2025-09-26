# src/video_management/dependencies.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.events.event_bus import EventBus
from src.metrics.application.metrics_service import MetricsService
from src.storage.infrastructure.dependencies import StorageServiceFactory
from .container import VideoContainer

def bootstrap_video_module(
    db_session: AsyncSession,
    storage_service_factory: StorageServiceFactory,
    event_bus: EventBus,
    metrics_service: MetricsService,
) -> VideoContainer:
    """Initializes and returns the container for the video management module."""
    return VideoContainer(
        db_session=db_session,
        storage_service_factory=storage_service_factory,
        event_bus=event_bus,
        metrics_service=metrics_service,
    )

# src/video_management/bootstrap.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.metrics.application.metrics_service import MetricsService
from src.shared.events.event_bus import EventBus
from src.storage.infrastructure.dependencies import StorageServiceFactory
from src.video_management.application.commands.upload_video_command_handler import UploadVideoCommandHandler
from src.video_management.application.queries.video_queries import VideoQueries
from src.video_management.application.video_service import VideoService
from src.video_management.infrastructure.video_repository import VideoRepository

def bootstrap_video_module(
    db_session: AsyncSession,
    storage_service_factory: StorageServiceFactory,
    event_bus: EventBus,
    metrics_service: MetricsService,
) -> Dict[str, Any]:
    """Constructs and returns the services for the video_management module."""
    video_repository = VideoRepository(db=db_session)
    video_queries = VideoQueries(video_repository=video_repository)
    
    upload_video_handler = UploadVideoCommandHandler(
        storage_service_factory=storage_service_factory,
        event_bus=event_bus,
        video_repository=video_repository,
        metrics_service=metrics_service
    )

    video_service = VideoService(
        upload_video_handler=upload_video_handler,
        video_repository=video_repository,
        storage_service_factory=storage_service_factory,
        video_queries=video_queries,
        event_bus=event_bus
    )

    return {
        "video_repository": video_repository,
        "video_queries": video_queries,
        "video_service": video_service,
    }

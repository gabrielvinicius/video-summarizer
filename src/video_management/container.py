# src/video_management/container.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.events.event_bus import EventBus
from src.metrics.application.metrics_service import MetricsService
from src.storage.infrastructure.dependencies import StorageServiceFactory
from src.video_management.application.video_service import VideoService
from src.video_management.application.commands.upload_video_command_handler import UploadVideoCommandHandler
from src.video_management.application.queries.video_queries import VideoQueries
from src.video_management.infrastructure.video_repository import VideoRepository


class VideoContainer:
    """Container for the video management module's dependencies."""
    def __init__(
        self,
        db_session: AsyncSession,
        storage_service_factory: StorageServiceFactory,
        event_bus: EventBus,
        metrics_service: MetricsService,
    ):
        self.repository = VideoRepository(db=db_session)
        self.queries = VideoQueries(video_repository=self.repository)
        
        upload_handler = UploadVideoCommandHandler(
            storage_service_factory=storage_service_factory,
            event_bus=event_bus,
            video_repository=self.repository,
            metrics_service=metrics_service
        )

        self.service = VideoService(
            upload_video_handler=upload_handler,
            video_repository=self.repository,
            storage_service_factory=storage_service_factory,
            video_queries=self.queries,
            event_bus=event_bus
        )

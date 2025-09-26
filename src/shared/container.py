from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

# Import cross-context dependencies explicitly
from src.auth.infrastructure.user_repository import UserRepository

# Shared
from src.shared.events.event_bus import get_event_bus

# Video
from src.video_management.application.video_service import VideoService
from src.video_management.application.commands.upload_video_command_handler import UploadVideoCommandHandler
from src.video_management.application.queries.video_queries import VideoQueries
from src.video_management.infrastructure.dependencies import get_video_repository

# Storage
from src.storage.infrastructure.dependencies import get_storage_service_factory

# Transcription
from src.transcription.application.queries.transcription_queries import TranscriptionQueries
from src.transcription.infrastructure.dependencies import get_speech_recognition_service_factory, get_transcription_repository

# Summarization
from src.summarization.application.summarization_service import SummarizationService
from src.summarization.application.queries.summary_queries import SummaryQueries
from src.summarization.infrastructure.dependencies import get_summarizer_service_factory
from src.summarization.infrastructure.summary_repository import SummaryRepository

# Analytics
from src.analytics.application.queries.analytics_queries import AnalyticsQueries
from src.analytics.config.settings import AnalyticsSettings
from src.analytics.infrastructure.analytics_repository import AnalyticsRepository

# Metrics
from src.metrics.application.metrics_service import MetricsService
from src.metrics.infrastructure.prometheus_provider import PrometheusMetricsProvider

# Notifications
from src.notifications.application.notification_service import NotificationService
from src.notifications.application.commands.send_notification_command_handler import SendNotificationCommandHandler
from src.notifications.application.queries.notification_queries import NotificationQueries
from src.notifications.config.settings import SmtpSettings
from src.notifications.infrastructure.notification_repository import NotificationRepository
from src.notifications.infrastructure.smtp_adapter import SMTPAdapter
from src.notifications.infrastructure.sms_adapter import SmsAdapter
from src.notifications.infrastructure.webhook_adapter import WebhookAdapter


class ApplicationContainer:
    def __init__(self):
        self.services: Dict[str, Any] = {}

    async def initialize(self, db_session: AsyncSession, user_repository: UserRepository):
        self.services["event_bus"] = get_event_bus()
        self.services["storage_service_factory"] = get_storage_service_factory()
        self.services["speech_recognition_service_factory"] = get_speech_recognition_service_factory()
        self.services["summarizer_service_factory"] = get_summarizer_service_factory()

        self._setup_metrics_services()
        self._setup_analytics_services(db_session)
        # Pass the explicit dependency to the notification setup
        self._setup_notification_services(db_session, user_repository)
        await self._setup_video_services(db_session)
        await self._setup_transcription_services(db_session)
        await self._setup_summarization_services(db_session)

        await self._register_event_handlers()

    def _setup_metrics_services(self) -> None:
        self.services["metrics_provider"] = PrometheusMetricsProvider()
        self.services["metrics_service"] = MetricsService(provider=self.services["metrics_provider"])

    def _setup_analytics_services(self, db_session: AsyncSession) -> None:
        self.services["analytics_repository"] = AnalyticsRepository(db_session)
        self.services["analytics_settings"] = AnalyticsSettings()
        self.services["analytics_queries"] = AnalyticsQueries(
            analytics_repo=self.services["analytics_repository"],
            settings=self.services["analytics_settings"]
        )

    def _setup_notification_services(self, db_session: AsyncSession, user_repository: UserRepository) -> None:
        smtp_settings = SmtpSettings()
        self.services["email_adapter"] = SMTPAdapter(host=smtp_settings.smtp_host, port=smtp_settings.smtp_port, username=smtp_settings.smtp_user, password=smtp_settings.smtp_password)
        self.services["sms_adapter"] = SmsAdapter()
        self.services["webhook_adapter"] = WebhookAdapter()
        self.services["notification_repository"] = NotificationRepository(db=db_session)
        send_notification_handler = SendNotificationCommandHandler(email_adapter=self.services["email_adapter"], sms_adapter=self.services["sms_adapter"], webhook_adapter=self.services["webhook_adapter"], notification_repository=self.services["notification_repository"], user_repository=user_repository)
        self.services["notification_service"] = NotificationService(send_notification_handler=send_notification_handler)
        self.services["notification_queries"] = NotificationQueries(notification_repository=self.services["notification_repository"])

    async def _setup_video_services(self, db_session: AsyncSession) -> None:
        self.services["video_repository"] = await get_video_repository(db_session)
        self.services["video_queries"] = VideoQueries(video_repository=self.services["video_repository"])
        upload_video_handler = UploadVideoCommandHandler(storage_service_factory=self.services["storage_service_factory"], event_bus=self.services["event_bus"], video_repository=self.services["video_repository"], metrics_service=self.services["metrics_service"])
        self.services["upload_video_handler"] = upload_video_handler
        video_service = VideoService(upload_video_handler=upload_video_handler, video_repository=self.services["video_repository"], storage_service_factory=self.services["storage_service_factory"], video_queries=self.services["video_queries"], event_bus=self.services["event_bus"])
        self.services["video_service"] = video_service

    async def _setup_transcription_services(self, db_session: AsyncSession) -> None:
        self.services["transcription_repository"] = await get_transcription_repository(db_session)
        self.services["transcription_queries"] = TranscriptionQueries(transcription_repository=self.services["transcription_repository"])

    async def _setup_summarization_services(self, db_session: AsyncSession) -> None:
        self.services["summary_repository"] = SummaryRepository(db_session)
        self.services["summary_queries"] = SummaryQueries(summary_repository=self.services["summary_repository"])
        self.services["summarization_service"] = SummarizationService(event_bus=self.services["event_bus"])

    async def _register_event_handlers(self) -> None:
        from src.transcription.application.event_handlers import register_event_handlers as register_transcription_handlers
        from src.notifications.application.event_handlers import register_event_handlers as register_notification_handlers
        from src.summarization.application.event_handlers import register_event_handlers as register_summary_handlers
        event_bus = self.services["event_bus"]
        await register_transcription_handlers(event_bus)
        await register_summary_handlers(event_bus)
        await register_notification_handlers(event_bus)


async def build_container(db_session: AsyncSession, user_repository: UserRepository) -> ApplicationContainer:
    container = ApplicationContainer()
    await container.initialize(db_session, user_repository)
    return container

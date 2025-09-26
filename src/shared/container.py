from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

# Shared
from src.shared.events.event_bus import get_event_bus

# Auth
from src.auth.application.auth_service import AuthService
from src.auth.application.commands.create_user_command_handler import CreateUserCommandHandler
from src.auth.application.commands.authenticate_user_command_handler import AuthenticateUserCommandHandler
from src.auth.application.queries.auth_queries import AuthQueries
from src.auth.config.settings import AuthSettings
from src.auth.infrastructure.user_repository import UserRepository

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
        self._services: Dict[str, Any] = {}

    async def initialize(self, db_session: AsyncSession) -> None:
        self._services["event_bus"] = get_event_bus()
        self._services["storage_service_factory"] = get_storage_service_factory()
        self._services["speech_recognition_service_factory"] = get_speech_recognition_service_factory()
        self._services["summarizer_service_factory"] = get_summarizer_service_factory()

        self._setup_metrics_services()
        self._setup_analytics_services(db_session)
        self._setup_auth_services(db_session)
        self._setup_notification_services(db_session)
        await self._setup_video_services(db_session)
        await self._setup_transcription_services(db_session)
        await self._setup_summarization_services(db_session)

        await self._register_event_handlers()

    def _setup_metrics_services(self) -> None:
        self._services["metrics_provider"] = PrometheusMetricsProvider()
        self._services["metrics_service"] = MetricsService(provider=self._services["metrics_provider"])

    def _setup_analytics_services(self, db_session: AsyncSession) -> None:
        """Configures analytics-related query handlers."""
        self._services["analytics_repository"] = AnalyticsRepository(db_session)
        self._services["analytics_settings"] = AnalyticsSettings()
        self._services["analytics_queries"] = AnalyticsQueries(
            analytics_repo=self._services["analytics_repository"],
            settings=self._services["analytics_settings"]
        )

    def _setup_auth_services(self, db_session: AsyncSession) -> None:
        self._services["user_repository"] = UserRepository(db=db_session)
        self._services["auth_settings"] = AuthSettings()
        create_user_handler = CreateUserCommandHandler(user_repository=self._services["user_repository"])
        authenticate_user_handler = AuthenticateUserCommandHandler(user_repository=self._services["user_repository"], settings=self._services["auth_settings"])
        self._services["auth_service"] = AuthService(create_user_handler=create_user_handler, authenticate_user_handler=authenticate_user_handler)
        self._services["auth_queries"] = AuthQueries(user_repository=self._services["user_repository"])

    def _setup_notification_services(self, db_session: AsyncSession) -> None:
        smtp_settings = SmtpSettings()
        self._services["email_adapter"] = SMTPAdapter(host=smtp_settings.smtp_host, port=smtp_settings.smtp_port, username=smtp_settings.smtp_user, password=smtp_settings.smtp_password)
        self._services["sms_adapter"] = SmsAdapter()
        self._services["webhook_adapter"] = WebhookAdapter()
        self._services["notification_repository"] = NotificationRepository(db=db_session)
        send_notification_handler = SendNotificationCommandHandler(email_adapter=self._services["email_adapter"], sms_adapter=self._services["sms_adapter"], webhook_adapter=self._services["webhook_adapter"], notification_repository=self._services["notification_repository"], user_repository=self._services["user_repository"])
        self._services["notification_service"] = NotificationService(send_notification_handler=send_notification_handler)
        self._services["notification_queries"] = NotificationQueries(notification_repository=self._services["notification_repository"])

    async def _setup_video_services(self, db_session: AsyncSession) -> None:
        self._services["video_repository"] = await get_video_repository(db_session)
        self._services["video_queries"] = VideoQueries(video_repository=self._services["video_repository"])
        upload_video_handler = UploadVideoCommandHandler(storage_service_factory=self._services["storage_service_factory"], event_bus=self._services["event_bus"], video_repository=self._services["video_repository"], metrics_service=self._services["metrics_service"])
        self._services["upload_video_handler"] = upload_video_handler
        video_service = VideoService(upload_video_handler=upload_video_handler, video_repository=self._services["video_repository"], storage_service_factory=self._services["storage_service_factory"], video_queries=self._services["video_queries"], event_bus=self._services["event_bus"])
        self._services["video_service"] = video_service

    async def _setup_transcription_services(self, db_session: AsyncSession) -> None:
        self._services["transcription_repository"] = await get_transcription_repository(db_session)
        self._services["transcription_queries"] = TranscriptionQueries(transcription_repository=self._services["transcription_repository"])

    async def _setup_summarization_services(self, db_session: AsyncSession) -> None:
        self._services["summary_repository"] = SummaryRepository(db_session)
        self._services["summary_queries"] = SummaryQueries(summary_repository=self._services["summary_repository"])
        self._services["summarization_service"] = SummarizationService(event_bus=self._services["event_bus"])

    async def _register_event_handlers(self) -> None:
        from src.transcription.application.event_handlers import register_event_handlers as register_transcription_handlers
        from src.notifications.application.event_handlers import register_event_handlers as register_notification_handlers
        from src.summarization.application.event_handlers import register_event_handlers as register_summary_handlers
        event_bus = self._services["event_bus"]
        await register_transcription_handlers(event_bus)
        await register_summary_handlers(event_bus)
        await register_notification_handlers(event_bus)

    def __getitem__(self, key: str) -> Any:
        return self._services[key]

    async def dispose(self) -> None:
        if "event_bus" in self._services and hasattr(self._services["event_bus"], "stop_listener"):
            await self._services["event_bus"].stop_listener()


async def build_container(db_session: AsyncSession) -> ApplicationContainer:
    container = ApplicationContainer()
    await container.initialize(db_session)
    return container

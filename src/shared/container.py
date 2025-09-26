from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

# Shared
from src.shared.events.event_bus import get_event_bus

# Auth
from src.auth.application.auth_service import AuthService
from src.auth.infrastructure.user_repository import UserRepository

# Video
from src.video_management.application.dependencies import get_video_service
from src.video_management.infrastructure.dependencies import get_video_repository

# Storage
from src.storage.infrastructure.dependencies import get_storage_service

# Transcription
from src.transcription.application.dependencies import get_transcription_service
from src.transcription.infrastructure.dependencies import get_speech_recognition, get_transcription_repository

# Summarization
from src.summarization.application.summarization_service import SummarizationService
from src.summarization.infrastructure.huggingface_summarizer import HuggingFaceSummarizer
from src.summarization.infrastructure.summary_repository import SummaryRepository

# Analytics
from src.analytics.application.analytics_service import AnalyticsService
from src.analytics.infrastructure.analytics_repository import AnalyticsRepository

# Metrics
from src.metrics.application.metrics_service import MetricsService
from src.metrics.infrastructure.prometheus_provider import PrometheusMetricsProvider

# Notifications
from src.notifications.application.notification_service import NotificationService
from src.notifications.config.settings import SmtpSettings
from src.notifications.infrastructure.notification_repository import NotificationRepository
from src.notifications.infrastructure.smtp_adapter import SMTPAdapter
from src.notifications.infrastructure.sms_adapter import SmsAdapter
from src.notifications.infrastructure.webhook_adapter import WebhookAdapter


class ApplicationContainer:
    def __init__(self):
        self._services: Dict[str, Any] = {}

    async def initialize(self, db_session: AsyncSession) -> None:
        """Initializes all services and dependencies."""
        # Shared services
        self._services["event_bus"] = get_event_bus()
        self._services["storage_service"] = await get_storage_service()

        # Setup services per context
        self._setup_metrics_services()
        self._setup_analytics_services(db_session)
        self._setup_auth_services(db_session)
        self._setup_notification_services(db_session) # Added notification setup
        await self._setup_video_services(db_session)
        await self._setup_transcription_services(db_session)
        await self._setup_summarization_services(db_session)

        # Register event handlers after all services are initialized
        await self._register_event_handlers()

    def _setup_metrics_services(self) -> None:
        self._services["metrics_provider"] = PrometheusMetricsProvider()
        self._services["metrics_service"] = MetricsService(provider=self._services["metrics_provider"])

    def _setup_analytics_services(self, db_session: AsyncSession) -> None:
        self._services["analytics_repository"] = AnalyticsRepository(db_session)
        self._services["analytics_service"] = AnalyticsService(analytics_repo=self._services["analytics_repository"])

    def _setup_auth_services(self, db_session: AsyncSession) -> None:
        self._services["user_repository"] = UserRepository(db=db_session)
        self._services["auth_service"] = AuthService(user_repository=self._services["user_repository"])

    def _setup_notification_services(self, db_session: AsyncSession) -> None:
        """Configures notification services."""
        smtp_settings = SmtpSettings()
        self._services["email_adapter"] = SMTPAdapter(
            host=smtp_settings.smtp_host,
            port=smtp_settings.smtp_port,
            username=smtp_settings.smtp_user,
            password=smtp_settings.smtp_password
        )
        self._services["sms_adapter"] = SmsAdapter() # Placeholder
        self._services["webhook_adapter"] = WebhookAdapter() # Placeholder
        self._services["notification_repository"] = NotificationRepository(db=db_session)
        self._services["notification_service"] = NotificationService(
            email_adapter=self._services["email_adapter"],
            sms_adapter=self._services["sms_adapter"],
            webhook_adapter=self._services["webhook_adapter"],
            notification_repository=self._services["notification_repository"],
            user_repository=self._services["user_repository"]
        )

    async def _setup_video_services(self, db_session: AsyncSession) -> None:
        self._services["video_repository"] = await get_video_repository(db_session)
        self._services["video_service"] = await get_video_service(db_session)

    async def _setup_transcription_services(self, db_session: AsyncSession) -> None:
        self._services["transcription_repository"] = await get_transcription_repository(db_session)
        self._services["speech_recognizer"] = await get_speech_recognition()
        self._services["transcription_service"] = await get_transcription_service(
            event_bus=self._services["event_bus"],
            storage_service=self._services["storage_service"],
            db=db_session,
            speech_recognition=self._services["speech_recognizer"]
        )

    async def _setup_summarization_services(self, db_session: AsyncSession) -> None:
        summary_repo = SummaryRepository(db_session)
        self._services["summary_repository"] = summary_repo
        self._services["summarizer"] = HuggingFaceSummarizer()
        self._services["summarization_service"] = SummarizationService(
            summarizer=self._services["summarizer"],
            summary_repo=summary_repo,
            transcription_service=self._services["transcription_service"],
            metrics_service=self._services["metrics_service"],
            analytics_service=self._services["analytics_service"],
            event_bus=self._services["event_bus"]
        )

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

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.auth.application.auth_service import AuthService
from src.auth.infrastructure.user_repository import UserRepository
from src.shared.events.event_bus import get_event_bus
# Transcrição
from src.transcription.infrastructure.dependencies import (
    get_speech_recognition,
    get_transcription_repository
)
from src.transcription.application.dependencies import get_transcription_service

# Sumarização
from src.summarization.infrastructure.summary_repository import SummaryRepository
from src.summarization.infrastructure.huggingface_summarizer import HuggingFaceSummarizer
from src.summarization.application.summarization_service import SummarizationService

# Vídeo
from src.video_management.infrastructure.dependencies import get_video_repository
from src.video_management.application.dependencies import get_video_service

# Armazenamento
from src.storage.infrastructure.dependencies import get_storage_service


class ApplicationContainer:
    def __init__(self):
        self._services: Dict[str, Any] = {}

    async def initialize(self, db_session: AsyncSession) -> None:
        """Inicializa todos os serviços e dependências"""
        # Configuração compartilhada
        self._services["event_bus"] = get_event_bus()
        self._services["storage_service"] = await get_storage_service()

        #Configuração de autenticação
        self._setup_auth_services(db_session)

        # Configuração de vídeo
        await self._setup_video_services(db_session)

        # Configuração de transcrição
        await self._setup_transcription_services(db_session)

        # Configuração de sumarização
        await self._setup_summarization_services(db_session)

        # Registro de event handlers
        await self._register_event_handlers()

    async def _setup_video_services(self, db_session: AsyncSession) -> None:
        """Configura serviços relacionados a vídeos"""
        self._services["video_repository"] = await get_video_repository(db_session)
        self._services["video_service"] = await get_video_service(db_session)

    async def _setup_transcription_services(self, db_session: AsyncSession) -> None:
        """Configura serviços de transcrição"""
        self._services["transcription_repository"] = await get_transcription_repository(db_session)
        self._services["speech_recognizer"] = await get_speech_recognition()
        self._services["transcription_service"] = await get_transcription_service(
            event_bus=self._services["event_bus"],
            storage_service=self._services["storage_service"],
            db=db_session,
            speech_recognition=self._services["speech_recognizer"]
        )

    async def _setup_summarization_services(self, db_session: AsyncSession) -> None:
        """Configura serviços de sumarização"""
        self._services["summary_repository"] = SummaryRepository(db_session)
        self._services["summarizer"] = HuggingFaceSummarizer()
        self._services["summarization_service"] = SummarizationService(
            summarizer=self._services["summarizer"],
            summary_repo=self._services["summary_repository"],
            transcription_service=self._services["transcription_service"]
        )

    def _setup_auth_services(self, db_session: AsyncSession) -> None:

        self._services["user_repository"] = UserRepository(db=db_session)
        self._services["auth_service"] = AuthService(user_repository=self._services["user_repository"])

    async def _register_event_handlers(self) -> None:
        """Registra todos os event handlers"""
        from src.transcription.application.event_handlers import (
            register_event_handlers as register_transcription_handlers
        )
        from src.notifications.application.event_handlers import (
            register_event_handlers as register_notification_handlers
        )
        from src.summarization.application.event_handlers import (
            register_event_handlers as register_summary_handlers
        )
        event_bus = self._services["event_bus"]
        await register_transcription_handlers(event_bus)
        await register_summary_handlers(event_bus)
        await register_notification_handlers(event_bus)



    def __getitem__(self, key: str) -> Any:
        """Acesso aos serviços através de chave"""
        return self._services[key]

    async def dispose(self) -> None:
        """Limpeza de recursos"""
        if "event_bus" in self._services and hasattr(self._services["event_bus"], "stop_listener"):
            await self._services["event_bus"].stop_listener()


async def build_container(db_session: AsyncSession) -> ApplicationContainer:
    """Factory function para criar e inicializar o container"""
    container = ApplicationContainer()
    await container.initialize(db_session)
    return container

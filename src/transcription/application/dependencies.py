from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.events.event_bus import get_event_bus, EventBus
from src.storage.application.storage_service import StorageService
from src.storage.infrastructure.dependencies import get_storage_service
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.infrastructure.dependencies import get_speech_recognition, get_transcription_repository
# Importação corrigida para o novo arquivo de interfaces
from src.transcription.infrastructure.interfaces import ISpeechRecognition
from src.video_management.application.dependencies import get_video_service


async def get_transcription_service(db: AsyncSession,
                                    event_bus: EventBus = get_event_bus(),
                                    storage_service: StorageService = get_storage_service(),
                                    speech_recognition: ISpeechRecognition = get_speech_recognition()
                                    ) -> TranscriptionService:
    return TranscriptionService(
        event_bus=event_bus,
        transcription_repository=await get_transcription_repository(db),
        video_service=await get_video_service(db),
        storage_service=storage_service,
        speech_recognition=speech_recognition
    )

from numba.cpython.heapq import assert_item_type_consistent_with_heap_type
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.events.event_bus import get_event_bus, EventBus
from src.storage.application.storage_service import StorageService
from src.storage.infrastructure.dependencies import get_storage_service
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.infrastructure.dependencies import get_speech_recognition, get_transcription_repository
from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.video_management.application.dependencies import get_video_service
from src.video_management.application.video_service import VideoService


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

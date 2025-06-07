from src.shared.events.event_bus import get_event_bus
from src.storage.application.storage_service import StorageService
from src.storage.infrastructure.dependencies import get_storage_service
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.infrastructure.dependencies import get_speech_recognition, get_transcription_repository
from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.video_management.application.dependencies import get_video_service
from src.video_management.application.video_service import VideoService

async def get_transcription_service() -> TranscriptionService:
    event_bus = get_event_bus()
    transcription_repository = await get_transcription_repository()
    video_service = await get_video_service()
    storage_service = await get_storage_service()
    speech_recognition = await get_speech_recognition()
    return TranscriptionService(
        event_bus=event_bus,
        transcription_repository=transcription_repository,
        video_service=video_service,
        storage_service=storage_service,
        speech_recognition=speech_recognition
    )
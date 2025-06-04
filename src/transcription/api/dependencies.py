# src/transcription/api/dependencies.py
from fastapi import Depends

from src.storage.application.storage_service import StorageService
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.infrastructure.dependencies import get_speech_recognition
from src.shared.events.event_bus import get_event_bus, EventBus
from src.shared.dependencies import get_transcription_repository, get_video_repository
from src.storage.infrastructure.dependencies import get_storage_service
from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.video_management.infrastructure.video_repository import VideoRepository


async def get_transcription_service(
    event_bus: EventBus = Depends(get_event_bus),
    transcription_repository: TranscriptionRepository = Depends(get_transcription_repository),
    video_repository: VideoRepository = Depends(get_video_repository),
    storage_service: StorageService = Depends(get_storage_service),
    speech_recognition: ISpeechRecognition = Depends(get_speech_recognition),
) -> TranscriptionService:
    return TranscriptionService(
        event_bus=event_bus,
        transcription_repository = transcription_repository,
        video_repository=video_repository,
        storage_service=storage_service,
        speech_recognition=speech_recognition
    )

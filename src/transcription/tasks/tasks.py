from celery import shared_task
from fastapi import Depends

from src.transcription.application.transcription_service import TranscriptionService
from src.shared.events.event_bus import get_event_bus
from src.transcription.infrastructure.whisper_adapter import WhisperTranscriber
from src.storage.infrastructure.dependencies import get_storage_service
#from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.shared.dependencies import get_video_repository,get_transcription_repository

@shared_task
def process_transcription_task(video_id: str, file_path: str):
    event_bus = get_event_bus()
    storage_service = get_storage_service()  # Injetar via configuração
    speech_adapter = WhisperTranscriber()  # Injetar Whisper/Google
    transcription_repo = Depends(get_transcription_repository)
    video_repo = Depends(get_video_repository)

    service = TranscriptionService(
        speech_adapter=speech_adapter,
        storage_service=storage_service,
        event_bus=event_bus,
        transcription_repository=transcription_repo,
        video_repository=video_repo
    )

    return service.process_transcription(video_id, file_path)
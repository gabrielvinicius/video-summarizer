from celery import shared_task
from src.transcription.application.transcription_service import TranscriptionService
from src.shared.events.event_bus import get_event_bus


@shared_task
def process_transcription_task(video_id: str, file_path: str):
    event_bus = get_event_bus()
    storage_service = ...  # Injetar via configuração
    speech_adapter = ...  # Injetar Whisper/Google
    transcription_repo = ...
    video_repo = ...

    service = TranscriptionService(
        speech_adapter=speech_adapter,
        storage_service=storage_service,
        event_bus=event_bus,
        transcription_repository=transcription_repo,
        video_repository=video_repo
    )

    return service.process_transcription(video_id, file_path)
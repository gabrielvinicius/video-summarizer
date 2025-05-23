from celery import shared_task
from ..application.summary_service import SummaryService
from src.shared.events.event_bus import get_event_bus


@shared_task
def generate_summary_task(transcription_id: str):
    event_bus = get_event_bus()
    llm_adapter = ...  # Injetar OpenAI/HuggingFace
    summary_repo = ...
    transcription_repo = ...
    video_repo = ...

    service = SummaryService(
        llm_adapter=llm_adapter,
        event_bus=event_bus,
        summary_repository=summary_repo,
        transcription_repository=transcription_repo,
        video_repository=video_repo
    )

    return service.generate_summary(transcription_id)
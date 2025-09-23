from celery import shared_task
from ..application.summarization_service import SummaryService
from src.shared.events.event_bus import EventBus
from ..infrastructure.huggingface_adapter import HuggingFaceSummarizer


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def generate_summary_task(transcription_id: str):
    event_bus = EventBus()
    llm_adapter = HuggingFaceSummarizer()  # Injetar OpenAI/HuggingFace
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
# src/metrics/application/metrics_service.py
from src.metrics.domain.metrics import MetricsProvider

class MetricsService:
    def __init__(self, provider: MetricsProvider):
        self.provider = provider

    def increment_video_upload(self, status: str):
        self.provider.increment_counter("VIDEO_UPLOADS_TOTAL", {"status": status})

    def increment_transcription(self, status: str):
        self.provider.increment_counter("TRANSCRIPTIONS_TOTAL", {"status": status})

    def increment_summarization(self, status: str):
        self.provider.increment_counter("SUMMARIZATIONS_TOTAL", {"status": status})

    def observe_transcription_duration(self, video_id: str, duration: float):
        self.provider.observe_histogram("TRANSCRIPTION_DURATION", duration, {"video_id": video_id})

    def observe_summarization_duration(self, video_id: str, duration: float):
        self.provider.observe_histogram("SUMMARIZATION_DURATION", duration, {"video_id": video_id})

    def observe_upload_duration (self , video_id: str, duration: float ):
        self.provider.observe_histogram("UPLOAD_DURATION", duration, {"video_id": video_id})
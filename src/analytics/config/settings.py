# src/analytics/config/settings.py
from pydantic_settings import BaseSettings

class AnalyticsSettings(BaseSettings):
    # Factor to multiply video duration for a default transcription time estimate
    default_transcription_factor: float = 1.0

    # Default fixed time in seconds for a summarization estimate
    default_summarization_seconds: float = 60.0

    # Number of analyzed videos required to consider the estimate as 'high' confidence
    high_confidence_threshold: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"
        env_prefix = "ANALYTICS_"

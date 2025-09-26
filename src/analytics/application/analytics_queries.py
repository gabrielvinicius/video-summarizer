# src/analytics/application/analytics_queries.py
from src.analytics.infrastructure.analytics_repository import AnalyticsRepository


class AnalyticsQueries:
    """Handles read-only operations for analytics."""
    def __init__(self, analytics_repo: AnalyticsRepository):
        self.analytics_repo = analytics_repo

    async def estimate_processing_time(self, video_duration_seconds: float) -> dict:
        """Estimates the total processing time based on video duration and historical data."""
        historical_data = await self.analytics_repo.get_average_processing_times()

        if historical_data["total_videos_analyzed"] == 0:
            # Default estimates (e.g., 1 min per minute of video for transcription, 10 seconds for summarization)
            transcription_est = video_duration_seconds * 1.0
            summarization_est = 60.0  # 1 minute fixed
            confidence = "low"
        else:
            # Use historical average times
            transcription_est = historical_data["transcription_avg_seconds"]
            summarization_est = historical_data["summarization_avg_seconds"]
            confidence = "high" if historical_data["total_videos_analyzed"] > 10 else "medium"

        total_est = transcription_est + summarization_est

        return {
            "estimated_total_seconds": total_est,
            "transcription_estimated_seconds": transcription_est,
            "summarization_estimated_seconds": summarization_est,
            "confidence_level": confidence
        }

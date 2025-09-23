# src/analytics/application/analytics_service.py
from src.analytics.infrastructure.analytics_repository import AnalyticsRepository

class AnalyticsService:
    def __init__(self, analytics_repo: AnalyticsRepository):
        self.analytics_repo = analytics_repo

    async def estimate_processing_time(self, video_duration_seconds: float) -> dict:
        """
        Estima o tempo total de processamento com base na duração do vídeo e no histórico.
        Args:
            video_duration_seconds: Duração do vídeo em segundos.
        Returns:
            dict: {
                "estimated_total_seconds": float,
                "transcription_estimated_seconds": float,
                "summarization_estimated_seconds": float,
                "confidence_level": str  # "high", "medium", "low"
            }
        """
        historical_data = await self.analytics_repo.get_average_processing_times()

        # Se não houver dados históricos, retorna estimativas padrão
        if historical_data["total_videos_analyzed"] == 0:
            # Estimativas padrão (ex: 1 minuto por minuto de vídeo para transcrição, 10 segundos para sumarização)
            transcription_est = video_duration_seconds * 1.0
            summarization_est = 60.0  # 1 minuto fixo
            confidence = "low"
        else:
            # Usa os tempos médios históricos
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
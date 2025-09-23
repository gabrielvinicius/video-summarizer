# src/analytics/infrastructure/analytics_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.video_management.domain.video import Video
from src.transcription.domain.transcription import Transcription
from src.summarization.domain.summary import Summary
from datetime import datetime

class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_average_processing_times(self) -> dict:
        """
        Calcula o tempo médio de processamento para transcrição e sumarização.
        Returns:
            dict: {
                "transcription_avg_seconds": float,
                "summarization_avg_seconds": float,
                "total_videos_analyzed": int
            }
        """
        # Consulta para obter vídeos COMPLETOS com transcrição e sumarização
        stmt = select(
            Video.created_at.label('video_created_at'),
            Transcription.created_at.label('transcription_created_at'),
            Transcription.processed_at.label('transcription_processed_at'),
            Summary.created_at.label('summary_created_at'),
            Summary.processed_at.label('summary_processed_at')
        ).join(
            Transcription, Video.id == Transcription.video_id
        ).join(
            Summary, Transcription.id == Summary.transcription_id
        ).where(
            Video.status == "COMPLETED",
            Transcription.status == "COMPLETED",
            Summary.status == "COMPLETED"
        )

        result = await self.db.execute(stmt)
        rows = result.fetchall()

        if not rows:
            return {
                "transcription_avg_seconds": 0.0,
                "summarization_avg_seconds": 0.0,
                "total_videos_analyzed": 0
            }

        total_transcription_time = 0.0
        total_summarization_time = 0.0
        valid_count = 0

        for row in rows:
            if row.transcription_processed_at and row.transcription_created_at:
                transcription_time = (row.transcription_processed_at - row.transcription_created_at).total_seconds()
                total_transcription_time += transcription_time

            if row.summary_processed_at and row.summary_created_at:
                summarization_time = (row.summary_processed_at - row.summary_created_at).total_seconds()
                total_summarization_time += summarization_time

            valid_count += 1

        return {
            "transcription_avg_seconds": total_transcription_time / valid_count if valid_count > 0 else 0.0,
            "summarization_avg_seconds": total_summarization_time / valid_count if valid_count > 0 else 0.0,
            "total_videos_analyzed": valid_count
        }
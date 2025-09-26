# src/analytics/infrastructure/analytics_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from src.video_management.domain.video import Video, VideoStatus
from src.transcription.domain.transcription import Transcription, TranscriptionStatus
from src.summarization.domain.summary import Summary, SummaryStatus


class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_average_processing_times(self) -> dict:
        """
        Calculates the average processing time for transcription and summarization
        by performing the aggregation directly in the database.
        """
        # Use SQLAlchemy's func module to generate AVG and COUNT aggregates.
        # Use func.extract('epoch', ...) to get the total seconds from a time interval.
        stmt = (
            select(
                func.avg(
                    func.extract('epoch', Transcription.processed_at - Transcription.created_at)
                ).label("transcription_avg_seconds"),
                func.avg(
                    func.extract('epoch', Summary.processed_at - Summary.created_at)
                ).label("summarization_avg_seconds"),
                func.count(Video.id).label("total_videos_analyzed")
            )
            .join(Transcription, Video.id == Transcription.video_id)
            .join(Summary, Transcription.id == Summary.transcription_id)
            .where(
                Video.status == VideoStatus.COMPLETED,
                Transcription.status == TranscriptionStatus.COMPLETED,
                Summary.status == SummaryStatus.COMPLETED
            )
        )

        result = await self.db.execute(stmt)
        row = result.first()

        if not row or row.total_videos_analyzed == 0:
            return {
                "transcription_avg_seconds": 0.0,
                "summarization_avg_seconds": 0.0,
                "total_videos_analyzed": 0
            }

        return {
            "transcription_avg_seconds": float(row.transcription_avg_seconds or 0.0),
            "summarization_avg_seconds": float(row.summarization_avg_seconds or 0.0),
            "total_videos_analyzed": int(row.total_videos_analyzed or 0)
        }

# src/shared/dependencies.py

from typing import Generator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import Session
# from src.shared.infrastructure.database import AsyncSessionLocal
from src.auth.infrastructure.user_repository import UserRepository
from src.storage.application.storage_service import StorageService
from src.video_management.infrastructure.video_repository import VideoRepository
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.summarization.infrastructure.summary_repository import SummaryRepository
from src.notifications.infrastructure.notification_repository import NotificationRepository
from src.shared.infrastructure.database import get_db


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_video_repository(db: AsyncSession = Depends(get_db)) -> VideoRepository:
    return VideoRepository(db)


async def get_transcription_repository(db: AsyncSession = Depends(get_db)) -> TranscriptionRepository:
    return TranscriptionRepository(db)


async def get_summary_repository(db: AsyncSession = Depends(get_db)) -> SummaryRepository:
    return SummaryRepository(db)


async def get_notification_repository(db: AsyncSession = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)

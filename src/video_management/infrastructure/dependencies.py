# from typing import Any, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

# from src.shared.infrastructure.database import get_db
from src.video_management.infrastructure.video_repository import VideoRepository


async def get_video_repository(db: AsyncSession) -> VideoRepository | None:
    if db is not None:
        print("Obtendo repositório de vídeo")
        return VideoRepository(db)
    return None
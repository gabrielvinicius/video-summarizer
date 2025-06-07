from typing import Any, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database import get_db
from src.video_management.infrastructure.video_repository import VideoRepository


async def get_video_repository() -> VideoRepository | None:
    async for db in get_db():
        return VideoRepository(db)
    return None
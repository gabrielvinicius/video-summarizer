from fastapi import Request, Depends
from typing import Annotated, Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.container import ApplicationContainer
from src.shared.infrastructure.database import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[Any, Any]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_container(request: Request) -> ApplicationContainer:
    return request.app.state.container


def get_service(service_name: str):
    async def _get_service(
            container: Annotated[ApplicationContainer, Depends(get_container)]
    ):
        return container[service_name]

    return _get_service


# Specific service dependencies for route injection
get_auth_service = get_service("auth_service")
get_notification_service = get_service("notification_service")

# Video
get_video_service = get_service("video_service") # For Commands
get_video_queries = get_service("video_queries") # For Queries

# Summarization
get_summarization_service = get_service("summarization_service") # For Commands
get_summary_queries = get_service("summary_queries") # For Queries

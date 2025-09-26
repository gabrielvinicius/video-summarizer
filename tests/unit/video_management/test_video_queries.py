# tests/unit/video_management/test_video_queries.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.video_management.application.queries.video_queries import VideoQueries
from src.video_management.domain.video import Video


@pytest.fixture
def mock_video_repository():
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_video_by_id(mock_video_repository):
    """Tests retrieving a video by its ID."""
    # Arrange
    video_id = uuid4()
    expected_video = Video(id=video_id, user_id="user1", file_path="path/to/video.mp4", storage_provider="local")
    mock_video_repository.find_by_id.return_value = expected_video

    queries = VideoQueries(video_repository=mock_video_repository)

    # Act
    result = await queries.get_video_by_id(str(video_id))

    # Assert
    assert result == expected_video
    mock_video_repository.find_by_id.assert_awaited_once_with(video_id)


@pytest.mark.asyncio
async def test_list_user_videos(mock_video_repository):
    """Tests listing videos for a specific user."""
    # Arrange
    user_id = uuid4()
    expected_videos = [
        Video(id=uuid4(), user_id=str(user_id), file_path="path/1.mp4", storage_provider="local"),
        Video(id=uuid4(), user_id=str(user_id), file_path="path/2.mp4", storage_provider="s3"),
    ]
    mock_video_repository.list_by_user.return_value = expected_videos

    queries = VideoQueries(video_repository=mock_video_repository)

    # Act
    result = await queries.list_user_videos(user_id=str(user_id), skip=0, limit=10)

    # Assert
    assert result == expected_videos
    mock_video_repository.list_by_user.assert_awaited_once_with(user_id=user_id, skip=0, limit=10)

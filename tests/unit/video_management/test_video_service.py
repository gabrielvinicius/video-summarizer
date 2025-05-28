import pytest
from unittest.mock import AsyncMock
from src.video_management.application.video_service import VideoService
from src.video_management.domain.video import VideoStatus

@pytest.fixture
def mock_storage():
    return AsyncMock()

@pytest.fixture
def mock_event_bus():
    return AsyncMock()

@pytest.fixture
def mock_repository():
    return AsyncMock()

@pytest.fixture
def video_service(mock_storage, mock_event_bus, mock_repository):
    return VideoService(
        storage_service=mock_storage,
        event_bus=mock_event_bus,
        video_repository=mock_repository,
    )

@pytest.mark.asyncio
async def test_upload_video(video_service, mock_repository, mock_event_bus, mock_storage):
    # Arrange
    user_id = "user123"
    file_data = b"dummy video content"
    filename = "test.mp4"

    # Act
    video = await video_service.upload_video(user_id, file_data, filename)

    # Assert
    assert video.user_id == user_id
    assert video.file_path.startswith(f"videos/{user_id}/")
    assert video.status == VideoStatus.UPLOADED
    mock_storage.upload.assert_awaited_once()
    mock_event_bus.publish.assert_awaited_once()
    mock_repository.save.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_video_by_id(video_service, mock_repository):
    # Arrange
    video_id = "vid123"
    mock_video = AsyncMock()
    mock_repository.find_by_id.return_value = mock_video

    # Act
    result = await video_service.get_video_by_id(video_id)

    # Assert
    assert result == mock_video
    mock_repository.find_by_id.assert_awaited_once_with(video_id)

@pytest.mark.asyncio
async def test_list_all_videos(video_service, mock_repository):
    # Arrange
    videos = [AsyncMock(), AsyncMock()]
    mock_repository.list_all.return_value = videos

    # Act
    result = await video_service.list_all_videos(skip=0, limit=10)

    # Assert
    assert result == videos
    mock_repository.list_all.assert_awaited_once_with(0, 10)

@pytest.mark.asyncio
async def test_list_user_videos(video_service, mock_repository):
    # Arrange
    user_id = "user123"
    videos = [AsyncMock()]
    mock_repository.list_by_user.return_value = videos

    # Act
    result = await video_service.list_user_videos(user_id)

    # Assert
    assert result == videos
    mock_repository.list_by_user.assert_awaited_once_with(user_id)

# tests/unit/video_management/test_upload_video_handler.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.video_management.application.commands.upload_video_command import UploadVideoCommand
from src.video_management.application.commands.upload_video_command_handler import UploadVideoCommandHandler
from src.shared.events.domain_events import VideoUploaded
from src.video_management.domain.video import Video


@pytest.fixture
def mock_storage_service():
    return AsyncMock()

@pytest.fixture
def mock_storage_factory(mock_storage_service):
    return MagicMock(return_value=mock_storage_service)

@pytest.fixture
def mock_event_bus():
    return AsyncMock()

@pytest.fixture
def mock_video_repository():
    return AsyncMock()

@pytest.fixture
def mock_metrics_service():
    return AsyncMock()


@pytest.mark.asyncio
async def test_upload_video_handler_success(
    mock_storage_factory,
    mock_event_bus,
    mock_video_repository,
    mock_metrics_service,
    mock_storage_service,
):
    """Tests the successful handling of an UploadVideoCommand."""
    # Arrange
    handler = UploadVideoCommandHandler(
        storage_service_factory=mock_storage_factory,
        event_bus=mock_event_bus,
        video_repository=mock_video_repository,
        metrics_service=mock_metrics_service,
    )
    command = UploadVideoCommand(
        user_id="user1",
        file=b"test_video_content",
        filename="test.mp4",
        storage_provider="local"
    )

    # Act
    result_video = await handler.handle(command)

    # Assert
    # 1. Ensure the correct storage provider was created and used
    mock_storage_factory.assert_called_once_with("local")
    mock_storage_service.upload.assert_awaited_once()

    # 2. Ensure the video entity was saved correctly
    mock_video_repository.save.assert_awaited_once()
    saved_video: Video = mock_video_repository.save.await_args.args[0]
    assert saved_video.user_id == command.user_id
    assert saved_video.storage_provider == command.storage_provider

    # 3. Ensure the correct event was published
    mock_event_bus.publish.assert_awaited_once()
    published_event: VideoUploaded = mock_event_bus.publish.await_args.args[0]
    assert isinstance(published_event, VideoUploaded)
    assert published_event.video_id == str(saved_video.id)

    # 4. Ensure metrics were observed
    mock_metrics_service.observe_upload_duration.assert_awaited_once()

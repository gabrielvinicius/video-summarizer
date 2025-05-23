import pytest
from unittest.mock import AsyncMock, MagicMock
from src.video_management.application.video_service import VideoService
from src.video_management.domain.video import VideoStatus


@pytest.mark.asyncio
async def test_upload_video():
    mock_storage = AsyncMock()
    mock_event_bus = AsyncMock()
    mock_repo = MagicMock()

    video_service = VideoService(mock_storage, mock_event_bus, mock_repo)

    user_id = "user-123"
    file_data = b"fake-video-data"
    filename = "video.mp4"

    video = await video_service.upload_video(user_id, file_data, filename)

    assert video.status == VideoStatus.UPLOADED
    mock_storage.upload.assert_awaited_once()
    mock_event_bus.publish.assert_awaited_once_with("video_uploaded", {
        "video_id": video.id,
        "file_path": video.file_path,
        "user_id": user_id
    })
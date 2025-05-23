import pytest
from unittest.mock import AsyncMock, MagicMock
from src.transcription.application.transcription_service import TranscriptionService


@pytest.mark.asyncio
async def test_process_transcription_success():
    mock_speech = AsyncMock(return_value="Texto transcrito")
    mock_storage = AsyncMock()
    mock_event_bus = AsyncMock()
    mock_transcription_repo = MagicMock()
    mock_video_repo = MagicMock()

    service = TranscriptionService(
        speech_adapter=mock_speech,
        storage_service=mock_storage,
        event_bus=mock_event_bus,
        transcription_repository=mock_transcription_repo,
        video_repository=mock_video_repo
    )

    transcription = await service.process_transcription("video-123", "path/to/video.mp4")

    assert transcription.status == "COMPLETED"
    mock_speech.transcribe.assert_awaited_once()
    mock_event_bus.publish.assert_awaited_once()
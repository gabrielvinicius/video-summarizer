# tests/unit/transcription/test_process_transcription_handler.py
import pytest
from unittest.mock import AsyncMock, patch
from pybreaker import CircuitBreakerError

from src.transcription.application.commands.process_transcription_command import ProcessTranscriptionCommand
from src.transcription.application.commands.process_transcription_command_handler import ProcessTranscriptionCommandHandler
from src.video_management.domain.video import Video, VideoStatus
from src.transcription.domain.transcription import Transcription, TranscriptionStatus
from src.shared.events.domain_events import TranscriptionStarted, TranscriptionCompleted, TranscriptionFailed

@pytest.fixture
def handler_mocks():
    """Sets up mocks for the ProcessTranscriptionCommandHandler dependencies."""
    return {
        "speech_recognition": AsyncMock(),
        "storage_service": AsyncMock(),
        "event_bus": AsyncMock(),
        "transcription_repository": AsyncMock(),
        "video_queries": AsyncMock(),
        "video_repository": AsyncMock(),
        "metrics_service": AsyncMock(),
    }

@pytest.mark.asyncio
@patch("src.transcription.application.commands.process_transcription_command_handler.get_circuit_breaker")
async def test_handle_new_transcription_success(mock_get_breaker, handler_mocks):
    """Tests the successful processing of a new transcription."""
    # Arrange
    video = Video(id="vid1", status=VideoStatus.UPLOADED, file_path="audio.mp3", storage_provider="local")
    handler_mocks["video_queries"].get_by_id.return_value = video
    handler_mocks["transcription_repository"].find_by_video_id.return_value = None
    handler_mocks["storage_service"].download.return_value = (b"audio_data", "audio.mp3")
    handler_mocks["speech_recognition"].transcribe.return_value = "Transcribed text"

    # Mock the circuit breaker to execute the call directly
    mock_breaker = AsyncMock()
    mock_breaker.call_async.return_value = "Transcribed text"
    mock_get_breaker.return_value = mock_breaker

    handler = ProcessTranscriptionCommandHandler(**handler_mocks)
    command = ProcessTranscriptionCommand(video_id="vid1", provider="whisper", language="en")

    # Act
    result = await handler.handle(command)

    # Assert
    assert result.status == TranscriptionStatus.COMPLETED
    assert result.text == "Transcribed text"
    assert video.status == VideoStatus.COMPLETED # Check final state

    handler_mocks["video_repository"].save.assert_awaited()
    mock_breaker.call_async.assert_awaited_once()

@pytest.mark.asyncio
@patch("src.transcription.application.commands.process_transcription_command_handler.get_circuit_breaker")
async def test_handle_transcription_failure(mock_get_breaker, handler_mocks):
    """Tests failure handling when the speech recognition service fails."""
    # Arrange
    video = Video(id="vid1", status=VideoStatus.UPLOADED, file_path="audio.mp3", storage_provider="local")
    handler_mocks["video_queries"].get_by_id.return_value = video
    handler_mocks["transcription_repository"].find_by_video_id.return_value = None
    handler_mocks["storage_service"].download.return_value = (b"audio_data", "audio.mp3")

    # Mock the circuit breaker to raise an error
    mock_breaker = AsyncMock()
    mock_breaker.call_async.side_effect = RuntimeError("External service failed")
    mock_get_breaker.return_value = mock_breaker

    handler = ProcessTranscriptionCommandHandler(**handler_mocks)
    command = ProcessTranscriptionCommand(video_id="vid1", provider="whisper", language="en")

    # Act & Assert
    with pytest.raises(RuntimeError, match="External service failed"):
        await handler.handle(command)

    # Assert that the video and transcription are marked as FAILED
    assert video.status == VideoStatus.FAILED
    handler_mocks["video_repository"].save.assert_awaited()
    saved_transcription = handler_mocks["transcription_repository"].save.await_args.args[0]
    assert saved_transcription.status == TranscriptionStatus.FAILED
    assert "External service failed" in saved_transcription.error_message
    assert isinstance(handler_mocks["event_bus"].publish.await_args.args[0], TranscriptionFailed)

# tests/unit/transcription/test_transcription_service.py
import pytest
import numpy as np
from unittest.mock import AsyncMock

from src.shared.events.domain_events import TranscriptionStarted, TranscriptionCompleted, TranscriptionFailed
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.domain.transcription import Transcription, TranscriptionStatus
from src.transcription.infrastructure.whisper_speech_recognition import WhisperTranscriber
from src.video_management.application.video_service import VideoService
from src.video_management.domain.video import Video, VideoStatus

# Import in-memory mocks
from tests.mocks.in_memory_event_bus import InMemoryEventBus
from tests.mocks.in_memory_storage import InMemoryStorage
from tests.mocks.in_memory_transcription_repository import InMemoryTranscriptionRepository
from tests.mocks.in_memory_video_repository import InMemoryVideoRepository


@pytest.fixture
def service_mocks():
    """Sets up mocks for all service dependencies."""
    return {
        "speech_recognition": AsyncMock(),
        "storage_service": AsyncMock(),
        "event_bus": AsyncMock(),
        "transcription_repo": AsyncMock(),
        "video_service": AsyncMock(),
        "metrics_service": AsyncMock(),
        "analytics_service": AsyncMock(),
    }


@pytest.fixture
def transcription_service(service_mocks):
    return TranscriptionService(**service_mocks)


@pytest.mark.asyncio
async def test_process_new_transcription_success(transcription_service, service_mocks):
    """Tests the successful flow for a new transcription."""
    video_id = "vid1"
    video = Video(id=video_id, status=VideoStatus.UPLOADED, file_path="audio.mp3")
    transcription = Transcription(id="trans1", video_id=video_id, status=TranscriptionStatus.PROCESSING)

    service_mocks["video_service"].get_video_by_id.return_value = video
    service_mocks["transcription_repo"].find_by_video_id.return_value = None
    service_mocks["transcription_repo"].save.return_value = transcription
    service_mocks["storage_service"].download.return_value = (b"audio_data", "audio.mp3")
    service_mocks["speech_recognition"].transcribe.return_value = "Transcribed text"

    result = await transcription_service.process_transcription(video_id)

    assert result.status == TranscriptionStatus.COMPLETED
    assert result.text == "Transcribed text"
    published_events = [call.args[0] for call in service_mocks["event_bus"].publish.await_args_list]
    assert any(isinstance(event, TranscriptionCompleted) for event in published_events)


@pytest.mark.asyncio
async def test_process_transcription_with_language(transcription_service, service_mocks):
    """Tests that the language parameter is correctly passed to the speech recognition service."""
    video_id = "vid1"
    language = "es"
    video = Video(id=video_id, status=VideoStatus.UPLOADED, file_path="audio.mp3")

    service_mocks["video_service"].get_video_by_id.return_value = video
    service_mocks["transcription_repo"].find_by_video_id.return_value = None
    service_mocks["storage_service"].download.return_value = (b"audio_data", "audio.mp3")
    service_mocks["speech_recognition"].transcribe.return_value = "Texto transcrito"

    await transcription_service.process_transcription(video_id, language=language)

    service_mocks["speech_recognition"].transcribe.assert_awaited_with(b"audio_data", language=language)


@pytest.mark.asyncio
async def test_idempotency_for_completed_transcription(transcription_service, service_mocks):
    """Tests that a completed transcription is not re-processed, but the event is re-published."""
    video_id = "vid1"
    existing_transcription = Transcription(id="trans1", video_id=video_id, status=TranscriptionStatus.COMPLETED, text="Existing text")
    service_mocks["transcription_repo"].find_by_video_id.return_value = existing_transcription

    result = await transcription_service.process_transcription(video_id)

    assert result == existing_transcription
    service_mocks["speech_recognition"].transcribe.assert_not_awaited()
    service_mocks["event_bus"].publish.assert_awaited_once()
    assert isinstance(service_mocks["event_bus"].publish.await_args.args[0], TranscriptionCompleted)


@pytest.mark.asyncio
async def test_transcription_failure_handling(transcription_service, service_mocks):
    """Tests failure handling when the speech recognition service fails."""
    video_id = "vid1"
    video = Video(id=video_id, status=VideoStatus.UPLOADED, file_path="audio.mp3")
    transcription = Transcription(id="trans1", video_id=video_id, status=TranscriptionStatus.PROCESSING)

    service_mocks["video_service"].get_video_by_id.return_value = video
    service_mocks["transcription_repo"].find_by_video_id.return_value = transcription
    service_mocks["storage_service"].download.return_value = (b"audio_data", "audio.mp3")
    service_mocks["speech_recognition"].transcribe.side_effect = RuntimeError("Transcription failed")

    with pytest.raises(RuntimeError, match="Transcription failed"):
        await transcription_service.process_transcription(video_id)

    saved_transcription = service_mocks["transcription_repo"].save.await_args.args[0]
    assert saved_transcription.status == TranscriptionStatus.FAILED
    assert isinstance(service_mocks["event_bus"].publish.await_args.args[0], TranscriptionFailed)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_transcription_flow():
    """A full integration test with in-memory dependencies."""
    # Arrange: Set up real services with in-memory implementations
    video_repo = InMemoryVideoRepository()
    transcription_repo = InMemoryTranscriptionRepository()
    storage = InMemoryStorage()
    event_bus = InMemoryEventBus()
    metrics_service = AsyncMock()
    analytics_service = AsyncMock()
    # Use a real Whisper transcriber, but with a tiny model for speed
    speech_recognition = WhisperTranscriber("tiny")

    video_service = VideoService(
        storage_service=storage,
        event_bus=event_bus,
        video_repository=video_repo,
        metrics_service=metrics_service
    )

    service = TranscriptionService(
        speech_recognition=speech_recognition,
        storage_service=storage,
        event_bus=event_bus,
        transcription_repository=transcription_repo,
        video_service=video_service,
        metrics_service=metrics_service,
        analytics_service=analytics_service
    )

    # Arrange: Create a video and a dummy audio file
    video = Video(id="test_video", user_id="user1", file_path="test_audio.wav", status=VideoStatus.UPLOADED)
    await video_repo.save(video)

    # 1 second of silence
    wav_bytes = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    await storage.upload("test_audio.wav", wav_bytes)

    # Act: Process the transcription
    result = await service.process_transcription("test_video")

    # Assert: Check the results
    assert result.status == TranscriptionStatus.COMPLETED
    assert isinstance(result.text, str)

    # Assert: Check that the correct event was published
    published_events = event_bus.get_events(TranscriptionCompleted)
    assert len(published_events) == 1
    assert published_events[0].video_id == "test_video"
    assert published_events[0].transcription_id == result.id

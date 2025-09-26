# tests/unit/transcription/test_transcription_queries.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.transcription.application.queries.transcription_queries import TranscriptionQueries
from src.transcription.domain.transcription import Transcription


@pytest.fixture
def mock_transcription_repository():
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_by_id(mock_transcription_repository):
    """Tests retrieving a transcription by its ID."""
    # Arrange
    transcription_id = str(uuid4())
    expected_transcription = Transcription(id=transcription_id, video_id=str(uuid4()))
    mock_transcription_repository.find_by_id.return_value = expected_transcription

    queries = TranscriptionQueries(transcription_repository=mock_transcription_repository)

    # Act
    result = await queries.get_by_id(transcription_id)

    # Assert
    assert result == expected_transcription
    mock_transcription_repository.find_by_id.assert_awaited_once_with(transcription_id)


@pytest.mark.asyncio
async def test_get_by_video_id(mock_transcription_repository):
    """Tests retrieving a transcription by its video ID."""
    # Arrange
    video_id = str(uuid4())
    expected_transcription = Transcription(id=str(uuid4()), video_id=video_id)
    mock_transcription_repository.find_by_video_id.return_value = expected_transcription

    queries = TranscriptionQueries(transcription_repository=mock_transcription_repository)

    # Act
    result = await queries.get_by_video_id(video_id)

    # Assert
    assert result == expected_transcription
    mock_transcription_repository.find_by_video_id.assert_awaited_once_with(video_id)

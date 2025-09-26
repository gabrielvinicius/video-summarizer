# tests/unit/summarization/test_summary_queries.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.summarization.application.queries.summary_queries import SummaryQueries
from src.summarization.domain.summary import Summary


@pytest.fixture
def mock_summary_repository():
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_by_id(mock_summary_repository):
    """Tests retrieving a summary by its ID."""
    # Arrange
    summary_id = str(uuid4())
    expected_summary = Summary(id=summary_id, transcription_id=str(uuid4()))
    mock_summary_repository.find_by_id.return_value = expected_summary

    queries = SummaryQueries(summary_repository=mock_summary_repository)

    # Act
    result = await queries.get_by_id(summary_id)

    # Assert
    assert result == expected_summary
    mock_summary_repository.find_by_id.assert_awaited_once_with(summary_id)


@pytest.mark.asyncio
async def test_get_by_transcription_id(mock_summary_repository):
    """Tests retrieving a summary by its transcription ID."""
    # Arrange
    transcription_id = str(uuid4())
    expected_summary = Summary(id=str(uuid4()), transcription_id=transcription_id)
    mock_summary_repository.find_by_transcription_id.return_value = expected_summary

    queries = SummaryQueries(summary_repository=mock_summary_repository)

    # Act
    result = await queries.get_by_transcription_id(transcription_id)

    # Assert
    assert result == expected_summary
    mock_summary_repository.find_by_transcription_id.assert_awaited_once_with(transcription_id)

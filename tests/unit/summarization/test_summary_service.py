# tests/unit/summarization/test_summary_service.py
import pytest
from unittest.mock import AsyncMock

from src.shared.events.domain_events import SummarizationRequested
from src.summarization.application.summarization_service import SummarizationService


@pytest.fixture
def mock_event_bus():
    return AsyncMock()


@pytest.mark.asyncio
async def test_request_summary_publishes_event(mock_event_bus):
    """Tests that the SummarizationService facade correctly publishes a SummarizationRequested event."""
    # Arrange
    service = SummarizationService(event_bus=mock_event_bus)
    transcription_id = "trans1"
    provider = "huggingface"

    # Act
    await service.request_summary(transcription_id, provider)

    # Assert
    mock_event_bus.publish.assert_awaited_once()
    published_event = mock_event_bus.publish.await_args.args[0]
    assert isinstance(published_event, SummarizationRequested)
    assert published_event.transcription_id == transcription_id
    assert published_event.provider == provider

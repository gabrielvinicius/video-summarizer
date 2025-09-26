# tests/unit/summarization/test_summary_service.py
import pytest
from unittest.mock import AsyncMock

from src.shared.events.domain_events import SummaryRequested, SummarizationProgress
from src.summarization.application.summarization_service import SummarizationService
from src.summarization.domain.summary import Summary, SummaryStatus
from src.transcription.domain.transcription import Transcription


@pytest.fixture
def service_mocks():
    """Sets up mocks for the SummarizationService dependencies."""
    return {
        "summarizer": AsyncMock(),
        "summary_repo": AsyncMock(),
        "transcription_service": AsyncMock(),
        "metrics_service": AsyncMock(),
        "analytics_service": AsyncMock(),
        "event_bus": AsyncMock(),
    }


@pytest.fixture
def summarization_service(service_mocks):
    return SummarizationService(**service_mocks)


@pytest.mark.asyncio
async def test_request_summary_publishes_event(summarization_service, service_mocks):
    """Tests that request_summary correctly publishes a SummaryRequested event."""
    # Arrange
    video_id = "vid1"
    user_id = "user1"
    language = "es"

    # Act
    await summarization_service.request_summary(video_id, user_id, language)

    # Assert
    service_mocks["event_bus"].publish.assert_awaited_once()
    published_event = service_mocks["event_bus"].publish.await_args.args[0]
    assert isinstance(published_event, SummaryRequested)
    assert published_event.video_id == video_id
    assert published_event.user_id == user_id
    assert published_event.language == language


@pytest.mark.asyncio
async def test_process_summary_for_new_summary(summarization_service, service_mocks):
    """Tests the successful processing of a new summary."""
    # Arrange
    transcription_id = "trans1"
    transcription = Transcription(id=transcription_id, text="This is a long transcription text.")
    summarized_text = "This is a summary."

    service_mocks["summary_repo"].find_by_transcription_id.return_value = None
    service_mocks["transcription_service"].get_transcription_by_id.return_value = transcription
    service_mocks["analytics_service"].estimate_processing_time.return_value = {"estimated_total_seconds": 60}
    service_mocks["summarizer"].summarize.return_value = summarized_text

    # Act
    result = await summarization_service.process_summary(transcription_id)

    # Assert
    assert result.status == SummaryStatus.COMPLETED
    assert result.text == summarized_text

    # Verify calls and events
    service_mocks["summary_repo"].save.assert_awaited()
    service_mocks["summarizer"].summarize.assert_awaited_with(transcription.text)

    published_events = [call.args[0] for call in service_mocks["event_bus"].publish.await_args_list]
    assert len(published_events) == 2  # Progress 25% and 75%
    assert any(isinstance(event, SummarizationProgress) and event.progress == 25 for event in published_events)
    assert any(isinstance(event, SummarizationProgress) and event.progress == 75 for event in published_events)


@pytest.mark.asyncio
async def test_process_summary_for_existing_completed_summary(summarization_service, service_mocks):
    """Tests that a completed summary is returned directly without reprocessing."""
    # Arrange
    transcription_id = "trans1"
    existing_summary = Summary(
        transcription_id=transcription_id,
        status=SummaryStatus.COMPLETED,
        text="An existing summary."
    )
    service_mocks["summary_repo"].find_by_transcription_id.return_value = existing_summary

    # Act
    result = await summarization_service.process_summary(transcription_id)

    # Assert
    assert result == existing_summary
    service_mocks["transcription_service"].get_transcription_by_id.assert_not_awaited()
    service_mocks["summarizer"].summarize.assert_not_awaited()
    service_mocks["event_bus"].publish.assert_not_awaited()

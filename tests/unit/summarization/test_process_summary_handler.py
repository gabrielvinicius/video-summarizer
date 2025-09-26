# tests/unit/summarization/test_process_summary_handler.py
import pytest
from unittest.mock import AsyncMock

from src.summarization.application.commands.process_summary_command import ProcessSummaryCommand
from src.summarization.application.commands.process_summary_command_handler import ProcessSummaryCommandHandler
from src.summarization.domain.summary import Summary, SummaryStatus
from src.transcription.domain.transcription import Transcription
from src.shared.events.domain_events import SummarizationProgress

@pytest.fixture
def handler_mocks():
    """Sets up mocks for the ProcessSummaryCommandHandler dependencies."""
    return {
        "summarizer": AsyncMock(),
        "summary_repo": AsyncMock(),
        "transcription_queries": AsyncMock(),
        "metrics_service": AsyncMock(),
        "analytics_queries": AsyncMock(),
        "event_bus": AsyncMock(),
    }

@pytest.mark.asyncio
async def test_process_new_summary_success(handler_mocks):
    """Tests the successful processing of a new summary."""
    # Arrange
    transcription_id = "trans1"
    provider = "huggingface"
    transcription = Transcription(id=transcription_id, text="This is a long transcription text.")
    summarized_text = "This is a summary."

    handler_mocks["summary_repo"].find_by_transcription_id.return_value = None
    handler_mocks["transcription_queries"].get_by_id.return_value = transcription
    handler_mocks["analytics_queries"].estimate_processing_time.return_value = {"estimated_total_seconds": 60}
    handler_mocks["summarizer"].summarize.return_value = summarized_text

    handler = ProcessSummaryCommandHandler(**handler_mocks)
    command = ProcessSummaryCommand(transcription_id=transcription_id, provider=provider)

    # Act
    result = await handler.handle(command)

    # Assert
    assert result.status == SummaryStatus.COMPLETED
    assert result.text == summarized_text
    assert result.provider == provider

    handler_mocks["summary_repo"].save.assert_awaited()
    handler_mocks["summarizer"].summarize.assert_awaited_with(transcription.text)

    published_events = [call.args[0] for call in handler_mocks["event_bus"].publish.await_args_list]
    assert any(isinstance(event, SummarizationProgress) for event in published_events)

@pytest.mark.asyncio
async def test_process_summary_for_existing_completed_summary(handler_mocks):
    """Tests that a completed summary is returned directly without reprocessing."""
    # Arrange
    transcription_id = "trans1"
    provider = "huggingface"
    existing_summary = Summary(transcription_id=transcription_id, status=SummaryStatus.COMPLETED, text="An existing summary.")
    handler_mocks["summary_repo"].find_by_transcription_id.return_value = existing_summary

    handler = ProcessSummaryCommandHandler(**handler_mocks)
    command = ProcessSummaryCommand(transcription_id=transcription_id, provider=provider)

    # Act
    result = await handler.handle(command)

    # Assert
    assert result == existing_summary
    handler_mocks["summarizer"].summarize.assert_not_awaited()

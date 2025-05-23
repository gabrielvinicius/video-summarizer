import pytest
from unittest.mock import AsyncMock, MagicMock
from src.summarization.application.summary_service import SummaryService


@pytest.mark.asyncio
async def test_generate_summary_success():
    mock_llm = AsyncMock(return_value="Resumo gerado")
    mock_event_bus = AsyncMock()
    mock_summary_repo = MagicMock()
    mock_transcription_repo = MagicMock()
    mock_video_repo = MagicMock()

    service = SummaryService(
        llm_adapter=mock_llm,
        event_bus=mock_event_bus,
        summary_repository=mock_summary_repo,
        transcription_repository=mock_transcription_repo,
        video_repository=mock_video_repo
    )

    summary = await service.generate_summary("transcription-123")

    assert summary.status == "COMPLETED"
    mock_llm.generate_summary.assert_awaited_once()
    mock_event_bus.publish.assert_awaited_once()
# src/summarization/bootstrap.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.shared.events.event_bus import EventBus
from src.summarization.application.queries.summary_queries import SummaryQueries
from src.summarization.application.summarization_service import SummarizationService
from src.summarization.infrastructure.summary_repository import SummaryRepository

def bootstrap_summarization_module(
    db_session: AsyncSession,
    event_bus: EventBus,
) -> Dict[str, Any]:
    """Constructs and returns the services for the summarization module."""
    summary_repository = SummaryRepository(db=db_session)
    summary_queries = SummaryQueries(summary_repository=summary_repository)
    summarization_service = SummarizationService(event_bus=event_bus)

    return {
        "summary_repository": summary_repository,
        "summary_queries": summary_queries,
        "summarization_service": summarization_service,
    }

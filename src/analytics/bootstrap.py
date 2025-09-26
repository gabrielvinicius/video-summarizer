# src/analytics/bootstrap.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.analytics.application.queries.analytics_queries import AnalyticsQueries
from src.analytics.config.settings import AnalyticsSettings
from src.analytics.infrastructure.analytics_repository import AnalyticsRepository

def bootstrap_analytics_module(db_session: AsyncSession) -> Dict[str, Any]:
    """Constructs and returns the query services for the analytics module."""
    analytics_repository = AnalyticsRepository(db=db_session)
    analytics_settings = AnalyticsSettings()
    analytics_queries = AnalyticsQueries(
        analytics_repo=analytics_repository,
        settings=analytics_settings
    )

    return {
        "analytics_repository": analytics_repository,
        "analytics_queries": analytics_queries,
    }

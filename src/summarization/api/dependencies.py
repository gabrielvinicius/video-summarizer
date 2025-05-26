from fastapi import Depends
from sqlalchemy.orm import Session
from src.shared.infrastructure.database import get_db
from src.summarization.application.summary_service import SummaryService
from src.summarization.infrastructure.summary_repository import SummaryRepository


def get_summary_service(db: Session = Depends(get_db)) -> SummaryService:
    repo = SummaryRepository(db)
    return SummaryService(summary_repo=repo)

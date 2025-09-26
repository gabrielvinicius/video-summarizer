from fastapi import APIRouter, Depends, HTTPException

from src.shared.dependencies import get_summarization_service
from src.summarization.application.summarization_service import SummarizationService
from .schemas import SummaryResponse

router = APIRouter(prefix="/summaries", tags=["Summaries"])


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary_by_id(summary_id: str, service: SummarizationService = Depends(get_summarization_service)):
    """Retrieves a summary by its ID."""
    summary = await service.summary_repo.find_by_id(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary

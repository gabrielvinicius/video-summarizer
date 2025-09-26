from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
from src.shared.dependencies import get_summarization_service
from src.summarization.application.summarization_service import SummarizationService
from .schemas import SummaryResponse, SummaryRequest

router = APIRouter(prefix="/summaries", tags=["Summaries"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def request_summary(
    summary_request: SummaryRequest,
    service: SummarizationService = Depends(get_summarization_service),
    _: User = Depends(get_current_user) # Ensures the user is authenticated
):
    """Requests an asynchronous summarization for a given transcription."""
    await service.request_summary(
        transcription_id=str(summary_request.transcription_id),
        provider=summary_request.provider
    )
    return {"message": "Summarization request accepted"}


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary_by_id(summary_id: str, service: SummarizationService = Depends(get_summarization_service)):
    """Retrieves a summary by its ID."""
    summary = await service.summary_repo.find_by_id(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary

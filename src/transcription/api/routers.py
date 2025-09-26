from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
# Import the correct CQRS dependencies
from src.shared.dependencies import get_summarization_service, get_transcription_queries
from src.summarization.application.summarization_service import SummarizationService
from src.transcription.application.queries.transcription_queries import TranscriptionQueries
from .schemas import TranscriptionResponse

router = APIRouter(prefix="/transcriptions", tags=["Transcriptions"])


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription_by_id(
    transcription_id: str,
    queries: TranscriptionQueries = Depends(get_transcription_queries)
):
    """Retrieves a transcription by its ID."""
    transcription = await queries.get_by_id(transcription_id)

    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    return transcription


@router.post("/{transcription_id}/summarization", status_code=status.HTTP_202_ACCEPTED)
async def request_summary_for_transcription(
    transcription_id: str,
    provider: Optional[str] = Query("huggingface", description="The summarization provider to use."),
    queries: TranscriptionQueries = Depends(get_transcription_queries),
    summarization_service: SummarizationService = Depends(get_summarization_service),
    _: User = Depends(get_current_user),
):
    """Triggers an asynchronous summarization process for a given transcription."""
    transcription = await queries.get_by_id(transcription_id)

    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )

    # Use the summarization service to request a summary
    await summarization_service.request_summary(
        transcription_id=transcription_id,
        provider=provider
    )

    return {"message": "Summarization requested successfully"}

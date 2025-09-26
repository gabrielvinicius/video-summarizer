from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
from src.shared.dependencies import get_summarization_service, get_transcription_service
from src.summarization.application.summarization_service import SummarizationService
from src.transcription.application.transcription_service import TranscriptionService
from .schemas import TranscriptionResponse

router = APIRouter(prefix="/transcriptions", tags=["Transcriptions"])


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription_by_id(
    transcription_id: str,
    service: TranscriptionService = Depends(get_transcription_service)
):
    """Retrieves a transcription by its ID."""
    transcription = await service.get_transcription_by_id(transcription_id)

    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    return transcription


@router.post("/{transcription_id}/summarization", status_code=status.HTTP_202_ACCEPTED)
async def request_summary_for_transcription(
    transcription_id: str,
    current_user: User = Depends(get_current_user),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
    summarization_service: SummarizationService = Depends(get_summarization_service),
):
    """
    Triggers an asynchronous summarization process for a given transcription.
    """
    transcription = await transcription_service.get_transcription_by_id(transcription_id)

    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )

    # Use the summarization service to request a summary, which will handle the correct event flow.
    await summarization_service.request_summary(
        video_id=str(transcription.video_id),
        user_id=str(current_user.id),
        language="en"  # Defaulting to English, could be a parameter in the future
    )

    return {"message": "Summarization requested successfully"}

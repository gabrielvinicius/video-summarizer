from fastapi import APIRouter, Depends, HTTPException
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.api.dependencies import get_transcription_service

from .schemas import TranscriptionResponse

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(transcription_id: str, service: TranscriptionService = Depends(get_transcription_service)):
    transcription = service.transcription_repo.find_by_id(transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcrição não encontrada")
    return transcription


from fastapi import APIRouter, Depends, HTTPException, status
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.api.dependencies import get_transcription_service
from src.shared.events.event_bus import EventBus
from src.shared.events.event_bus import get_event_bus  # Importar a dependência correta

from .schemas import TranscriptionResponse
from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
        transcription_id: str,
        service: TranscriptionService = Depends(get_transcription_service)
):
    # Usar await com o método assíncrono
    transcription = await service.get_transcription_by_id(transcription_id)

    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcrição não encontrada"
        )
    return transcription


@router.post(  # Mudar para POST pois está disparando uma ação
    "/{transcription_id}/summarization",
    status_code=status.HTTP_202_ACCEPTED
)
async def summarization_transcription(
        transcription_id: str,
        current_user: User = Depends(get_current_user),
        service: TranscriptionService = Depends(get_transcription_service),
        event_bus: EventBus = Depends(get_event_bus)  # Injetar via dependência
):
    """
    Trigger asynchronous summarization for a transcription.
    """
    transcription = await service.get_transcription_by_id(transcription_id)

    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcrição não encontrada"
        )

    # Publicar o evento usando o event bus injetado
    await event_bus.publish("transcription_completed", {
        "video_id": transcription.video_id,
        "transcription_id": transcription.id
    })

    return {"message": "Sumarização iniciada com sucesso"}
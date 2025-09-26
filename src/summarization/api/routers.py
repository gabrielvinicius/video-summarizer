from fastapi import APIRouter, Depends, HTTPException

from src.shared.dependencies import get_summarization_service  # Importação corrigida
from src.summarization.application.summarization_service import SummarizationService
from .schemas import SummaryResponse

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(summary_id: str, service: SummarizationService = Depends(get_summarization_service)):
    summary = await service.summary_repo.find_by_id(summary_id)  # Corrigido com await
    if not summary:
        raise HTTPException(status_code=404, detail="Resumo não encontrado")
    return summary

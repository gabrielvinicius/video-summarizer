from fastapi import APIRouter, Depends, HTTPException
from src.summarization.application.summary_service import SummaryService
from src.summarization.api.dependencies import get_summary_service
from .schemas import SummaryResponse

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(summary_id: str, service: SummaryService = Depends(get_summary_service)):
    summary = service.summary_repo.find_by_id(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Resumo não encontrado")
    return summary

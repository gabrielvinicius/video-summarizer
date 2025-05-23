from fastapi import APIRouter, Depends, HTTPException
from ..application.summary_service import SummaryService
from .schemas import SummaryResponse

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(summary_id: str, service: SummaryService = Depends()):
    summary = service.summary_repo.find_by_id(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Resumo não encontrado")
    return summary

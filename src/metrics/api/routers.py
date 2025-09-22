# src/metrics/api/routers.py
from fastapi import APIRouter, Depends,Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


from src.metrics.application.metrics_service import MetricsService

router = APIRouter(tags=["Metrics"])

@router.get("/metrics")
async def get_metrics():
    """
    Endpoint para expor métricas no formato Prometheus.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
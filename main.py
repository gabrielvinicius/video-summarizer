import asyncio
import time

from fastapi import FastAPI, Depends, Request,Response
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Importe todas as rotas
from src.auth.api.routers import router as auth_router
from src.video_management.api.routers import router as video_router
from src.summarization.api.routers import router as summary_router
from src.notifications.api.routers import router as notification_router
from src.transcription.api.routers import router as transcription_router

# Importe dependências de banco de dados e container
from src.shared.container import build_container, ApplicationContainer
from src.shared.infrastructure.database import Base, engine, AsyncSessionLocal
# from src.shared.dependencies import get_db_session, get_container, get_video_service

# Importe event handlers
from src.transcription.application.event_handlers import register_event_handlers as register_transcription_handlers
from src.summarization.application.event_handlers import register_event_handlers as register_summary_handlers
from src.notifications.application.event_handlers import register_event_handlers as register_notification_handlers

# --- Métricas Prometheus (existentes) ---
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status_code']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Latency',
    ['method', 'endpoint']
)
# ----------------------------

# --- Novas Métricas de Negócio ---
# Contadores para operações de alto nível
VIDEO_UPLOADS_TOTAL = Counter(
    'video_uploads_total',
    'Total de vídeos enviados',
    ['status']  # status: success, failure
)

TRANSCRIPTIONS_TOTAL = Counter(
    'transcriptions_total',
    'Total de transcrições processadas',
    ['status']  # status: success, failure
)

SUMMARIZATIONS_TOTAL = Counter(
    'summarizations_total',
    'Total de sumarizações geradas',
    ['status']  # status: success, failure
)

# Histogramas para tempos de processamento
VIDEO_PROCESSING_DURATION = Histogram(
    'video_processing_duration_seconds',
    'Tempo total de processamento de um vídeo (upload + transcrição + sumarização)',
    ['stage']  # stage: transcription, summarization
)

# --- Novas Métricas de Duração por Serviço ---
TRANSCRIPTION_DURATION = Histogram(
    'transcription_duration_seconds',
    'Tempo de processamento da transcrição por vídeo',
    ['video_id']  # Etiqueta para rastrear por vídeo
)

SUMMARIZATION_DURATION = Histogram(
    'summarization_duration_seconds',
    'Tempo de processamento da sumarização por vídeo',
    ['video_id']  # Etiqueta para rastrear por vídeo
)
UPLOAD_DURATION = Histogram(
    'summarization_duration_seconds',
    'Tempo de processamento de upload por vídeo',
    ['video_id']  # Etiqueta para rastrear por vídeo
)
# ----------------------------
# Gauges para estado do sistema
ACTIVE_PROCESSES = Gauge(
    'active_video_processes',
    'Número de vídeos atualmente sendo processados'
)

# ----------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Criação das tabelas do banco de dados
    print("⏳ Criando tabelas do banco de dados...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Criação do container de dependências
    print("⚙️ Inicializando container de dependências...")
    async with AsyncSessionLocal() as session:
        container = await build_container(session)
        app.state.container = container

        # Registra event handlers
        # print("🔔 Registrando handlers de eventos...")
        # await register_transcription_handlers(container["event_bus"])
        # await register_summary_handlers(container["event_bus"])
        # await register_notification_handlers(container["event_bus"])

        # Inicia o event bus
        print("🚀 Iniciando barramento de eventos...")
        await container["event_bus"].start_listener()

        yield

        # Limpeza ao encerrar a aplicação
        print("🛑 Encerrando recursos...")
        await container.dispose()
        await engine.dispose()


app = FastAPI(
    title="API de Gerenciamento de Vídeos",
    description="API para upload, transcrição e sumarização de vídeos",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Middleware para Métricas ---
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path

    # Inicia o timer
    start_time = time.time()

    response = await call_next(request)

    # Calcula a latência
    latency = time.time() - start_time

    # Atualiza as métricas
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=response.status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

    return response
# ----------------------------

# --- Endpoint de Métricas ---
@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
# ----------------------------

# Função para injetar serviços nas rotas
def get_service(service_name: str):
    async def _get_service(request: Request):
        container = request.app.state.container
        return container[service_name]

    return _get_service


# Registra rotas com prefixos e tags organizadas
app.include_router(
    transcription_router,
    #prefix="/transcriptions",
    tags=["Transcrições"],
    dependencies=[Depends(get_service("transcription_service"))]
)
app.include_router(
    summary_router,
    #prefix="/summaries",
    tags=["Sumarizações"],
    dependencies=[Depends(get_service("summarization_service"))]
)
app.include_router(
    notification_router,
    #prefix="/notifications",
    tags=["Notificações"],
    dependencies=[Depends(get_service("event_bus"))]
)
app.include_router(
    auth_router,
    #prefix="/notifications",
    tags=["Autenticação"],
    dependencies=[Depends(get_service("event_bus"))]
)
app.include_router(
    video_router,
    #prefix="/notifications",
    tags=["Videos"],
    dependencies=[Depends(get_service("event_bus"))]
)


# Rota de saúde da aplicação
@app.get("/health", tags=["Sistema"])
async def health_check():
    return {
        "status": "healthy",
        "services": [
            "auth",
            "videos",
            "transcriptions",
            "summarizations",
            "notifications"
        ]
    }


# Middleware para log de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 Recebida requisição: {request.method} {request.url}")
    response = await call_next(request)
    print(f"📤 Respondendo: {response.status_code}")
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4,
        log_level="info",
        access_log=True
    )

import asyncio
import time

from fastapi import FastAPI, Depends, Request, Response
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Import routers
from src.auth.api.routers import router as auth_router
from src.video_management.api.routers import router as video_router
from src.summarization.api.routers import router as summary_router
from src.notifications.api.routers import router as notification_router
from src.transcription.api.routers import router as transcription_router
from src.metrics.api.routers import router as metrics_router
from src.providers.api.routers import router as providers_router # Added providers router

# Import container and database dependencies
from src.shared.container import build_container, ApplicationContainer
from src.shared.infrastructure.database import Base, engine, AsyncSessionLocal

# --- Prometheus Metrics ---
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

# --- Business Metrics ---
VIDEO_UPLOADS_TOTAL = Counter(
    'video_uploads_total',
    'Total videos uploaded',
    ['status']
)

TRANSCRIPTIONS_TOTAL = Counter(
    'transcriptions_total',
    'Total transcriptions processed',
    ['status']
)

SUMMARIZATIONS_TOTAL = Counter(
    'summarizations_total',
    'Total summaries generated',
    ['status']
)

# --- Processing Duration Histograms ---
UPLOAD_DURATION = Histogram(
    'upload_duration_seconds',
    'Upload processing time per video',
    ['video_id', 'provider']
)
TRANSCRIPTION_DURATION = Histogram(
    'transcription_duration_seconds',
    'Transcription processing time per video',
    ['video_id', 'provider']
)
SUMMARIZATION_DURATION = Histogram(
    'summarization_duration_seconds',
    'Summarization processing time per video',
    ['video_id', 'provider']
)

# --- System State Gauges ---
ACTIVE_PROCESSES = Gauge(
    'active_video_processes',
    'Number of videos currently being processed'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⏳ Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("⚙️ Initializing dependency container...")
    async with AsyncSessionLocal() as session:
        container = await build_container(session)
        app.state.container = container

        print("🚀 Starting event bus...")
        await container["event_bus"].start_listener()

        yield

        print("🛑 Shutting down resources...")
        await container.dispose()
        await engine.dispose()


app = FastAPI(
    title="Video Management API",
    description="API for uploading, transcribing, and summarizing videos",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# --- Middlewares ---
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status_code=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(latency)
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 Request received: {request.method} {request.url}")
    response = await call_next(request)
    print(f"📤 Responding: {response.status_code}")
    return response


# --- Endpoints ---
@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy"}


# --- Dependency Injection Helper ---
def get_service(service_name: str):
    async def _get_service(request: Request):
        return request.app.state.container[service_name]
    return _get_service


# --- Route Registration ---
app.include_router(providers_router)
app.include_router(auth_router)
app.include_router(video_router)
app.include_router(transcription_router)
app.include_router(summary_router)
app.include_router(notification_router)
app.include_router(metrics_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=4, log_level="info", access_log=True)

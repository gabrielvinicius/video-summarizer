import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# OpenTelemetry Imports
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from src.shared.infrastructure.tracing import configure_tracer

# --- Module Bootstrapping and Composition Root ---
from src.auth.dependencies import bootstrap_auth_module
from src.shared.container import build_container
from src.shared.infrastructure.database import Base, engine, AsyncSessionLocal

# API Routers
from src.auth.api.routers import router as auth_router
from src.metrics.api.routers import router as metrics_router
from src.notifications.api.routers import router as notification_router
from src.providers.api.routers import router as providers_router
from src.summarization.api.routers import router as summary_router
from src.transcription.api.routers import router as transcription_router
from src.video_management.api.routers import router as video_router


# --- Prometheus Metrics ---
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status_code'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Configure Observability
    configure_tracer("video-summarizer-api")

    # 2. Initialize Database
    print("⏳ Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 3. Initialize Modules and Compose Application (Composition Root)
    print("⚙️ Initializing modules and composing application...")
    async with AsyncSessionLocal() as session:
        # Bootstrap each module independently
        auth_container = bootstrap_auth_module(session)
        
        # Build the main container, injecting cross-context dependencies explicitly
        main_container = await build_container(session, user_repository=auth_container.user_repository)

        # Create a unified container for the application state
        app.state.container = {
            "auth_service": auth_container.service,
            "auth_queries": auth_container.queries,
            **main_container.services, # Add all other services
        }

        # 4. Start Background Services
        print("🚀 Starting event bus...")
        await app.state.container["event_bus"].start_listener()

        yield

        # 5. Clean up resources
        print("🛑 Shutting down resources...")
        await app.state.container["event_bus"].stop_listener()
        await engine.dispose()


app = FastAPI(
    title="Video Management API",
    description="API for uploading, transcribing, and summarizing videos",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Instrument the FastAPI app with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)


# --- Middlewares & Endpoints ---
# ... (Middlewares and other endpoints remain the same)


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

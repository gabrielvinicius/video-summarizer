import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.auth.api.routers import router as auth_router
from src.video_management.api.routers import router as video_router
from src.summarization.api.routers import router as summary_router
from src.notifications.api.routers import router as notification_router
from src.transcription.api.routers import router as transcription_router

from src.shared.infrastructure.database import Base, engine
from src.shared.events.event_bus import get_event_bus
from src.transcription.application.event_handlers import register_event_handlers as register_transcription_handlers
from src.summarization.application.event_handlers import register_event_handlers as register_summary_handlers
from src.notifications.application.event_handlers import register_event_handlers as register_notification_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização do banco de dados
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Configuração do barramento de eventos
    event_bus = get_event_bus()

    # Registro dos handlers de eventos
    await register_transcription_handlers(event_bus)
    await register_summary_handlers(event_bus)
    await register_notification_handlers(event_bus)

    # Inicia o listener do event bus
    await event_bus.start_listener()

    # Disponibiliza o event_bus no estado da aplicação
    app.state.event_bus = event_bus

    try:
        yield
    finally:
        # Encerramento limpo
        if hasattr(event_bus, "stop_listener"):
            await event_bus.stop_listener()
        await engine.dispose()


app = FastAPI(
    title="API de Gerenciamento de Vídeos",
    description="API para upload, transcrição e sumarização de vídeos",
    version="1.0.0",
    lifespan=lifespan
)

# Registra rotas com prefixos e tags organizadas
app.include_router(auth_router, prefix="/auth", tags=["Autenticação"])
app.include_router(video_router, prefix="/videos", tags=["Vídeos"])
app.include_router(
    transcription_router,
    prefix="/transcriptions",
    tags=["Transcrições"]
)
app.include_router(
    summary_router,
    prefix="/summaries",
    tags=["Sumarizações"]
)
app.include_router(
    notification_router,
    prefix="/notifications",
    tags=["Notificações"]
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4  # Aumenta o número de workers para produção
    )
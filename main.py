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

event_bus = get_event_bus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await register_transcription_handlers(event_bus)
    await register_summary_handlers(event_bus)
    await register_notification_handlers(event_bus)
    event_bus.start_listener()  # Use await se for async!
    yield
    # Shutdown logic (opcional)
    # await event_bus.stop_listener()  # Se você tiver esse método


app = FastAPI(lifespan=lifespan)

# Registra rotas
app.include_router(auth_router)
app.include_router(video_router)
app.include_router(transcription_router)
app.include_router(summary_router)
app.include_router(notification_router)

if __name__ == "__main__":
    import uvicorn

    # asyncio.run(engine.begin().__aenter__())  # Garante que crie tabelas se rodar direto este script
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

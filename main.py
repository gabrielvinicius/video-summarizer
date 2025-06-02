# main.py
import asyncio
from fastapi import FastAPI
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

app = FastAPI()

# Configuração do barramento de eventos
event_bus = get_event_bus()

# Registra handlers de eventos de todos os módulos
register_transcription_handlers(event_bus)
register_summary_handlers(event_bus)
register_notification_handlers(event_bus)

# Registra rotas
app.include_router(auth_router)
app.include_router(video_router)
app.include_router(transcription_router)
app.include_router(summary_router)
app.include_router(notification_router)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Inicializa o banco ao iniciar a aplicação
@app.on_event("startup")
async def on_startup():
    await init_models()
    event_bus.start_listener()  # <--- INICIA O OUVINTE DE EVENTOS


if __name__ == "__main__":
    import uvicorn
    asyncio.run(init_models())  # Garante que crie tabelas se rodar direto este script
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

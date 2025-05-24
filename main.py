from fastapi import FastAPI
from src.auth.api.routers import router as auth_router
from src.video_management.api.routers import router as video_router
from src.summarization.api.routers import router as summary_router
from src.notifications.api.routers import router as notification_router
from src.shared.infrastructure.database import Base, engine
from src.shared.events.event_bus import EventBus
from src.transcription.application.event_handlers import register_event_handlers as register_transcription_handlers
from src.summarization.application.event_handlers import register_event_handlers as register_summary_handlers
from src.notifications.application.event_handlers import register_event_handlers as register_notification_handlers

# Cria tabelas no banco de dados (para exemplo; em produção, use migrações)
Base.metadata.create_all(bind=engine)

# Configuração do barramento de eventos
event_bus = EventBus()

# Registra handlers de eventos de todos os módulos
register_transcription_handlers(event_bus)
register_summary_handlers(event_bus)
register_notification_handlers(event_bus)

app = FastAPI()

# Registra rotas
app.include_router(auth_router)
app.include_router(video_router)
app.include_router(summary_router)
app.include_router(notification_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
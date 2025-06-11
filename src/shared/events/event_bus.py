from celery import Celery
from typing import Dict, Callable, Any, Optional, Coroutine, Union
import json
import asyncio
import redis.asyncio as aioredis
import logging
from src.shared.config.broker_settings import BrokerSettings

# Configurações
settings = BrokerSettings()
logger = logging.getLogger(__name__)

# Celery worker configuration
celery = Celery(__name__, broker=settings.redis_url)
celery.conf.task_serializer = 'json'
celery.conf.result_serializer = 'json'
celery.conf.accept_content = ['json']
celery.conf.task_default_queue = 'default'
celery.conf.task_default_exchange = 'default'
celery.conf.task_default_routing_key = 'default'

celery.autodiscover_tasks([
    "src.transcription.tasks",
    "src.summarization.tasks",
    "src.notifications.tasks",
])

# Redis async client
redis_client = aioredis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True
)


class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, list[Callable[[Any], Union[None, Coroutine]]]] = {}
        self._listener_task: Optional[asyncio.Task] = None

    def subscribe(self, event_type: str, handler: Callable[[Any], Union[None, Coroutine]]):
        """Registra um handler local para determinado tipo de evento."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def publish(self, event_type: str, data: Any):
        """Publica evento no Redis (consumido pelo listener)."""
        try:
            await redis_client.publish(event_type, json.dumps(data, default=str))
        except TypeError as e:
            raise ValueError(f"Erro ao serializar payload: {e}")

    async def _listen(self):
        """Loop principal para escutar eventos Redis e despachar handlers."""
        while True:
            try:
                pubsub = redis_client.pubsub()
                await pubsub.subscribe(*self.subscribers.keys())

                async for message in pubsub.listen():
                    if message["type"] == "message":
                        event_type = message["channel"]
                        if isinstance(event_type, bytes):
                            event_type = event_type.decode()

                        data = json.loads(message["data"])

                        if event_type in self.subscribers:
                            for handler in self.subscribers[event_type]:
                                if asyncio.iscoroutinefunction(handler):
                                    await asyncio.create_task(handler(data))
                                else:
                                    handler(data)

            except Exception as e:
                logger.warning(f"[EventBus] Redis error: {e}. Retentando em 5s...")
                await asyncio.sleep(5)

    async def start_listener(self):
        """Inicia o listener de eventos Redis em segundo plano."""
        if not self._listener_task:
            self._listener_task = asyncio.create_task(self._listen())
            logger.info("[EventBus] Listener iniciado.")

    async def stop_listener(self):
        """Encerra conexões com Redis (opcional para shutdown elegante)."""
        try:
            await redis_client.close()
            logger.info("[EventBus] Redis client encerrado.")
        except Exception as e:
            logger.error(f"[EventBus] Falha ao encerrar Redis: {e}")


# Instância singleton
_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance

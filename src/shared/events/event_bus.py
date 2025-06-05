from celery import Celery
from typing import Dict, Callable, Any, Optional, Coroutine, Union
import json
import asyncio
import redis.asyncio as aioredis  # ✅ Cliente asyncio nativo
from src.shared.config.broker_settings import BrokerSettings

# Configurações
settings = BrokerSettings()

# Celery para workers assíncronos
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

# Cliente Redis asyncio
redis_client = aioredis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True
)


class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, list[Callable[[Any], Union[None, Coroutine]]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Any], Union[None, Coroutine]]):
        """Registra um handler para um tipo de evento"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def publish(self, event_type: str, data: Any):
        """Publica evento localmente e no Redis"""
        # Chamada local aos handlers
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                if asyncio.iscoroutinefunction(handler):
                    await asyncio.create_task(handler(data))  # Assíncrono
                else:
                    handler(data)  # Síncrono

        # Publica no Redis
        try:
            await redis_client.publish(event_type, json.dumps(data, default=str))
        except TypeError as e:
            raise ValueError(f"Erro ao serializar payload: {e}")

    def start_listener(self):
        """Inicia ouvinte de eventos via Redis"""
        async def listen():
            while True:
                try:
                    pubsub = redis_client.pubsub()
                    await pubsub.subscribe(*self.subscribers.keys())

                    async for message in pubsub.listen():
                        if message["type"] == "message":
                            event_type = message["channel"]
                            data = json.loads(message["data"])

                            if event_type in self.subscribers:
                                for handler in self.subscribers[event_type]:
                                    if asyncio.iscoroutinefunction(handler):
                                        await asyncio.create_task(handler(data))
                                    else:
                                        handler(data)
                except Exception as e:
                    print(f"[EventBus] Redis error: {e}. Tentando novamente em 5s...")
                    await asyncio.sleep(5)

        asyncio.create_task(listen())  # Executa listener de forma assíncrona


# Instância global singleton
_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance

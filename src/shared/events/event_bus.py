from celery import Celery
from typing import Dict, Callable, Any, Optional, Coroutine, Union, Type
import json
import asyncio
import redis.asyncio as aioredis
import logging

from src.shared.config.broker_settings import BrokerSettings
from src.shared.events.domain_events import DomainEvent  # Importação adicionada

# Configurações
settings = BrokerSettings()
logger = logging.getLogger(__name__)

# Celery (mantido para os tasks assíncronos)
celery = Celery(__name__, broker=settings.redis_url)
celery.conf.task_serializer = 'json'
celery.conf.result_serializer = 'json'
celery.conf.accept_content = ['json']
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
        self.subscribers: Dict[str, list[Callable[[Dict], Union[None, Coroutine]]]] = {}
        self._listener_task: Optional[asyncio.Task] = None

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[Dict], Union[None, Coroutine]]):
        """Registra um handler local para um tipo de evento de domínio."""
        event_name = event_type.__name__
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(handler)

    async def publish(self, event: DomainEvent):
        """Publica um evento de domínio no Redis."""
        event_type = event.__class__.__name__
        data = event.to_dict()
        try:
            await redis_client.publish(event_type, json.dumps(data, default=str))
        except TypeError as e:
            raise ValueError(f"Erro ao serializar o payload do evento: {e}")

    async def _listen(self):
        """Loop principal para escutar eventos Redis e despachar handlers."""
        # O restante do código não precisa de alteração, pois já trabalha com
        # o nome do evento como string e o payload como um dicionário JSON.
        while True:
            try:
                pubsub = redis_client.pubsub()
                if not self.subscribers:
                    await asyncio.sleep(1) # Evita loop ocupado se não houver assinantes
                    continue

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
                logger.warning(f"[EventBus] Erro no Redis: {e}. Tentando novamente em 5s...")
                await asyncio.sleep(5)

    async def start_listener(self):
        """Inicia o listener de eventos Redis em segundo plano."""
        if not self._listener_task:
            self._listener_task = asyncio.create_task(self._listen())
            logger.info("[EventBus] Listener iniciado.")

    async def stop_listener(self):
        """Encerra conexões com Redis."""
        try:
            if self._listener_task:
                self._listener_task.cancel()
            await redis_client.close()
            logger.info("[EventBus] Cliente Redis encerrado.")
        except Exception as e:
            logger.error(f"[EventBus] Falha ao encerrar Redis: {e}")


# Instância singleton
_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance

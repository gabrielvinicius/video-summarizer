# src/shared/events/event_bus.py

from celery import Celery
from typing import Dict, Callable, Any, Optional
import redis
import json
import threading
import time
import asyncio  # ✅ Importado para lidar com coroutines
from src.shared.config.broker_settings import BrokerSettings

settings = BrokerSettings()

celery = Celery(__name__, broker=settings.redis_url)
celery.autodiscover_tasks([
    "src.transcription.tasks",
    "src.summarization.tasks",
    "src.notifications.tasks",
])
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True
)


class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, list[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Any], None]):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def publish(self, event_type: str, data: Any):
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                if asyncio.iscoroutinefunction(handler):
                    await asyncio.create_task(handler(data))  # ✅ dispara a coroutine
                else:
                    handler(data)

        # Serializa para Redis (UUIDs devem ser convertidos para string antes)
        try:
            await redis_client.publish(event_type, json.dumps(data, default=str))  # ✅ default=str para UUIDs
        except TypeError as e:
            raise ValueError(f"Erro ao serializar payload: {e}")

    def start_listener(self):
        def run():
            while True:
                try:
                    pubsub = redis_client.pubsub()
                    pubsub.subscribe(*self.subscribers.keys())

                    for message in pubsub.listen():
                        if message["type"] == "message":
                            event_type = message["channel"]
                            data = json.loads(message["data"])
                            if event_type in self.subscribers:
                                for handler in self.subscribers[event_type]:
                                    if asyncio.iscoroutinefunction(handler):
                                        asyncio.create_task(handler(data))
                                    else:
                                        handler(data)
                except Exception as e:
                    print(f"[EventBus] Redis error: {e}. Retrying in 5s...")
                    time.sleep(5)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()


# Instância global singleton
_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance

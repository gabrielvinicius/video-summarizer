from celery import Celery
from typing import Dict, Callable, Any
import redis

celery = Celery(__name__, broker="redis://redis:6379/0")
redis_client = redis.Redis(host="redis", port=6379, db=0)


class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def publish(self, event_type: str, data: Any):
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                handler(data)
        # Publica no Redis para Celery
        redis_client.publish(event_type, str(data))


# Instância global do EventBus
event_bus = EventBus()

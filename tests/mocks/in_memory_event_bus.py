# tests/mocks/in_memory_event_bus.py
from typing import List, Dict, Callable, Any, Coroutine, Union, Type
from src.shared.events.domain_events import DomainEvent
from src.shared.events.event_bus import EventBus


class InMemoryEventBus(EventBus):
    def __init__(self):
        super().__init__()
        self.events: List[DomainEvent] = []

    async def publish(self, event: DomainEvent):
        """Stores the event in an in-memory list instead of publishing to Redis."""
        self.events.append(event)

    def get_events(self, event_type: Type[DomainEvent]) -> List[DomainEvent]:
        """Returns all recorded events of a specific type."""
        return [event for event in self.events if isinstance(event, event_type)]

    def clear(self):
        """Clears all recorded events."""
        self.events.clear()

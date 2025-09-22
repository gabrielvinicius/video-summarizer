# src/metrics/domain/metrics.py
from abc import ABC, abstractmethod
from enum import Enum

class MetricType(Enum):
    COUNTER = "counter"
    HISTOGRAM = "histogram"

class MetricsProvider(ABC):
    @abstractmethod
    def increment_counter(self, name: str, labels: dict = None):
        pass

    @abstractmethod
    def observe_histogram(self, name: str, value: float, labels: dict = None):
        pass
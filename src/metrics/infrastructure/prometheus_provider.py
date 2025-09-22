# src/metrics/infrastructure/prometheus_provider.py
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from src.metrics.domain.metrics import MetricsProvider

class PrometheusMetricsProvider(MetricsProvider):
    def __init__(self):
        # --- Métricas HTTP ---
        self.REQUEST_COUNT = Counter(
            'http_requests_total',
            'Total HTTP Requests',
            ['method', 'endpoint', 'status_code']
        )
        self.REQUEST_LATENCY = Histogram(
            'http_request_duration_seconds',
            'HTTP Request Latency',
            ['method', 'endpoint']
        )

        # --- Métricas de Negócio ---
        self.VIDEO_UPLOADS_TOTAL = Counter(
            'video_uploads_total',
            'Total de vídeos enviados',
            ['status']
        )
        self.TRANSCRIPTIONS_TOTAL = Counter(
            'transcriptions_total',
            'Total de transcrições processadas',
            ['status']
        )
        self.SUMMARIZATIONS_TOTAL = Counter(
            'summarizations_total',
            'Total de sumarizações geradas',
            ['status']
        )

        # --- Métricas de Duração por Serviço ---
        self.TRANSCRIPTION_DURATION = Histogram(
            'transcription_duration_seconds',
            'Tempo de processamento da transcrição por vídeo',
            ['video_id']
        )
        self.SUMMARIZATION_DURATION = Histogram(
            'summarization_duration_seconds',
            'Tempo de processamento da sumarização por vídeo',
            ['video_id']
        )

    def increment_counter(self, name: str, labels: dict = None):
        metric = getattr(self, name, None)
        if metric and isinstance(metric, Counter):
            if labels:
                metric.labels(**labels).inc()
            else:
                metric.inc()

    def observe_histogram(self, name: str, value: float, labels: dict = None):
        metric = getattr(self, name, None)
        if metric and isinstance(metric, Histogram):
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)
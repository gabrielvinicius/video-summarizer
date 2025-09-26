# src/shared/infrastructure/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.udp import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def configure_tracer(service_name: str):
    """Configures the global tracer for the application."""
    # Set the service name for all traces
    resource = Resource(attributes={
        SERVICE_NAME: service_name
    })

    # Initialize the TracerProvider with the resource
    provider = TracerProvider(resource=resource)

    # Configure the Jaeger exporter
    # By default, it sends traces to a Jaeger agent on localhost:6831 via UDP
    exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )

    # Use a BatchSpanProcessor to send spans in batches
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    # Set the configured provider as the global tracer provider
    trace.set_tracer_provider(provider)

    print(f"✅ OpenTelemetry tracing configured for service '{service_name}' sending to Jaeger on localhost:6831")

    return trace.get_tracer(__name__)

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from harp_daemon.settings.flask_settings import SERVICE_NAME, TracingConfig
tracer = None


def get_tracer():
    global tracer
    if not tracer:
        resource = Resource(attributes={"service.name": SERVICE_NAME})
        tracer = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer)
        tracer.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=TracingConfig.TEMPO_URL)))

    return tracer

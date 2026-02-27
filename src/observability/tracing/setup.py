from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from fastapi import FastAPI
import os

def setup_tracing(app: FastAPI, service_name: str = "ai-agent-hub"):
    """Initialize OpenTelemetry tracing with OTLP exporter."""
    
    # Создаём resource с информацией о сервисе
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("APP_VERSION", "dev"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })
    
    # Настраиваем TracerProvider
    provider = TracerProvider(resource=resource)
    
    # Настраиваем экспортёр (по умолчанию на localhost:4317)
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True,  # для dev-окружения
    )
    
    # Добавляем процессор для пакетной отправки
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    
    # Устанавливаем глобальный провайдер
    trace.set_tracer_provider(provider)
    
    # Инструментируем FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    return trace.get_tracer(__name__)

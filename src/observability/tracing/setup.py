"""OpenTelemetry tracing setup.

This module must be safe to import even when OpenTelemetry packages are not installed
(e.g., minimal/CI environments). In that case, setup_tracing() becomes a no-op and
returns a noop tracer.
"""

from __future__ import annotations

import os
from fastapi import FastAPI

# ---- Optional OpenTelemetry imports (safe for CI/minimal installs) ----
try:
    from opentelemetry import trace as _otel_trace  # type: ignore
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
    from opentelemetry.sdk.resources import Resource  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore

    OTEL_AVAILABLE = True
except Exception:  # pragma: no cover
    _otel_trace = None
    OTLPSpanExporter = None
    FastAPIInstrumentor = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    OTEL_AVAILABLE = False


class _NoopSpan:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _NoopTracer:
    def start_as_current_span(self, *args, **kwargs):
        return _NoopSpan()


class _NoopTrace:
    def get_tracer(self, *args, **kwargs):
        return _NoopTracer()

    def set_tracer_provider(self, *args, **kwargs):
        return None


# Public "trace" symbol, used by code/tests
trace = _otel_trace if _otel_trace is not None else _NoopTrace()


def setup_tracing(app: FastAPI, service_name: str = "ai-agent-hub"):
    """Initialize OpenTelemetry tracing with OTLP exporter.

    If OpenTelemetry is not installed, this function is a safe no-op and returns a noop tracer.
    """
    if not OTEL_AVAILABLE:
        # No-op in minimal/CI environments
        return trace.get_tracer(__name__)

    # Create resource with service info
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("APP_VERSION", "dev"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })

    provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True,
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    trace.set_tracer_provider(provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    return trace.get_tracer(__name__)

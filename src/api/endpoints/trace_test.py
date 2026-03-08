from fastapi import APIRouter
# Optional OpenTelemetry (CI may not install it)
try:
    from opentelemetry import trace as _otel_trace  # type: ignore
except Exception:  # pragma: no cover
    _otel_trace = None

class _NoopSpan:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

class _NoopTracer:
    def start_as_current_span(self, *args, **kwargs):
        return _NoopSpan()

class _TraceShim:
    def get_tracer(self, name: str):
        if _otel_trace is not None:
            return _otel_trace.get_tracer(name)
        return _NoopTracer()

trace = _TraceShim()

router = APIRouter(tags=["Test"])

@router.get("/api/v1/trace-test")
async def trace_test():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("test-span") as span:
        span.set_attribute("test.attribute", "hello")
        return {"status": "traced"}

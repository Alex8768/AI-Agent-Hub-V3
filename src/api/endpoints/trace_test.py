from fastapi import APIRouter
from opentelemetry import trace

router = APIRouter(tags=["Test"])

@router.get("/api/v1/trace-test")
async def trace_test():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("test-span") as span:
        span.set_attribute("test.attribute", "hello")
        return {"status": "traced"}

"""OpenTelemetry setup for the inbox agent.

Spans follow the OTel GenAI semantic conventions (experimental; see observability.md):
one `invoke_agent` root per email, a `chat` child per model call, an `execute_tool`
child per tool call. Export is OTLP/HTTP, configured by the standard OTEL_* env vars.

Email bodies, model output and tool arguments contain customer PII, so they are only
recorded when INBOX_TRACE_CONTENT=1 (dev). Production traces carry structure, counts,
IDs and flags only.
"""
import os

from opentelemetry import trace

CAPTURE_CONTENT = os.environ.get("INBOX_TRACE_CONTENT") == "1"

tracer = trace.get_tracer("inbox-agent")


def init_tracing() -> None:
    """Install an OTLP-exporting TracerProvider. Call once at process start.

    Spans go to OTEL_EXPORTER_OTLP_ENDPOINT (default http://localhost:4318), ideally
    a Collector. The SDK flushes on interpreter exit; short-lived workers should still
    call `trace.get_tracer_provider().shutdown()` before exiting.
    """
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", "inbox-agent"),
        "service.version": os.environ.get("APP_RELEASE", "dev"),
        "deployment.environment.name": os.environ.get("APP_ENV", "dev"),
    })
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

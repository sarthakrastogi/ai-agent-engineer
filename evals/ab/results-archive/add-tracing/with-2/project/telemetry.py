"""OpenTelemetry setup for the inbox agent.

Spans follow the OTel GenAI semantic conventions (experimental; pinned via
OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental). Exports OTLP/HTTP to the endpoint in
OTEL_EXPORTER_OTLP_ENDPOINT (default http://localhost:4318), normally a Collector.

Message/tool content is NOT recorded unless TRACE_CONTENT=1: customer emails carry PII.
"""
import atexit
import json
import os

from opentelemetry import trace

os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental")

tracer = trace.get_tracer("parcelly.inbox_agent")


def capture_content() -> bool:
    return os.environ.get("TRACE_CONTENT", "").lower() in ("1", "true", "yes")


def set_content(span, key: str, value) -> None:
    """Record content on a span only when content capture is enabled."""
    if capture_content():
        span.set_attribute(key, value if isinstance(value, str) else json.dumps(value, default=str))


def setup_tracing(service_name: str = "inbox-agent") -> None:
    """Install a TracerProvider exporting OTLP. Call once at process start-up.

    If the process already configures OpenTelemetry, skip this and let that provider be used.
    """
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.environ.get("RELEASE", "dev"),
        "deployment.environment.name": os.environ.get("DEPLOY_ENV", "dev"),
    })
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    atexit.register(provider.shutdown)  # flushes pending spans on exit

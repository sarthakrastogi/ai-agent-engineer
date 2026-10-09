"""OpenTelemetry setup for the inbox agent (GenAI semantic conventions, OTLP export).

Spans: invoke_agent inbox_agent -> chat {model} / execute_tool {name}.
Message content (email bodies, tool args/results) is PII and is only recorded when
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true. Keep it off in production.
"""
import json
import os

from opentelemetry import trace

# GenAI semconv is still in development; pin the variant we emit.
os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental")

RELEASE = os.environ.get("APP_RELEASE", "dev")
CAPTURE_CONTENT = os.environ.get(
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false").lower() == "true"

tracer = trace.get_tracer("parcelly.inbox_agent")


def setup_tracing(service_name: str = "inbox-agent"):
    """Install an OTLP-exporting TracerProvider. Call once at process start.

    Endpoint and headers come from the standard OTEL_EXPORTER_OTLP_* env vars
    (point them at an OTel Collector). Call `shutdown_tracing()` before exit.
    """
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=Resource.create({
        "service.name": service_name, "service.version": RELEASE}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    return provider


def shutdown_tracing():
    """Flush pending spans; required for scripts, workers and serverless handlers."""
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()


def set_content(span, key: str, value):
    """Record message content on `span` only when content capture is enabled."""
    if CAPTURE_CONTENT:
        span.set_attribute(key, value if isinstance(value, str) else json.dumps(value, default=str))

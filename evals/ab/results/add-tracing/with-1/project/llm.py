"""Thin wrapper over the Anthropic Messages API. Tests monkeypatch `_create`."""
import os

from opentelemetry.trace import SpanKind

from tracing import set_content, tracer

MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")


def _create(**kwargs):
    import anthropic  # imported lazily so tests run without the SDK

    return anthropic.Anthropic().messages.create(**kwargs)


def complete(system: str, messages: list[dict], tools: list[dict] | None = None,
             max_tokens: int = 1024):
    """Return the raw Messages API response (content blocks, stop_reason)."""
    kwargs = {"model": MODEL, "system": system, "messages": messages, "max_tokens": max_tokens}
    if tools:
        kwargs["tools"] = tools
    with tracer.start_as_current_span(f"chat {MODEL}", kind=SpanKind.CLIENT) as span:
        span.set_attributes({
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "anthropic",
            "gen_ai.request.model": MODEL,
            "gen_ai.request.max_tokens": max_tokens,
        })
        set_content(span, "gen_ai.input.messages", messages)
        resp = _create(**kwargs)
        usage = getattr(resp, "usage", None)
        span.set_attributes({
            "gen_ai.response.id": getattr(resp, "id", "") or "",
            "gen_ai.response.model": getattr(resp, "model", "") or "",
            "gen_ai.response.finish_reasons": [resp.stop_reason or ""],
            "gen_ai.usage.input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "gen_ai.usage.output_tokens": getattr(usage, "output_tokens", 0) or 0,
            "gen_ai.usage.cache_read.input_tokens":
                getattr(usage, "cache_read_input_tokens", 0) or 0,
            "gen_ai.usage.cache_creation.input_tokens":
                getattr(usage, "cache_creation_input_tokens", 0) or 0,
        })
        set_content(span, "gen_ai.output.messages", [_dump(b) for b in resp.content])
        return resp


def _dump(block):
    return block.model_dump() if hasattr(block, "model_dump") else block


def text_of(response) -> str:
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")

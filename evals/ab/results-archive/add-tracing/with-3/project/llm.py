"""Thin wrapper over the Anthropic Messages API. Tests monkeypatch `complete`."""
import json
import os

from tracing import CAPTURE_CONTENT, tracer

MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")


def complete(system: str, messages: list[dict], tools: list[dict] | None = None,
             max_tokens: int = 1024):
    """Return the raw Messages API response (content blocks, stop_reason)."""
    import anthropic  # imported lazily so tests run without the SDK

    with tracer.start_as_current_span(f"chat {MODEL}") as span:
        span.set_attributes({
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "anthropic",
            "gen_ai.request.model": MODEL,
            "gen_ai.request.max_tokens": max_tokens,
            "app.request.message_count": len(messages),
        })
        client = anthropic.Anthropic()
        kwargs = {"model": MODEL, "system": system, "messages": messages, "max_tokens": max_tokens}
        if tools:
            kwargs["tools"] = tools
        resp = client.messages.create(**kwargs)

        usage = resp.usage
        span.set_attributes({
            "gen_ai.response.id": resp.id,
            "gen_ai.response.model": resp.model,
            "gen_ai.response.finish_reasons": [resp.stop_reason or ""],
            "gen_ai.usage.input_tokens": usage.input_tokens,
            "gen_ai.usage.output_tokens": usage.output_tokens,
            "gen_ai.usage.cache_read.input_tokens": getattr(usage, "cache_read_input_tokens", None) or 0,
            "gen_ai.usage.cache_creation.input_tokens": getattr(usage, "cache_creation_input_tokens", None) or 0,
        })
        if CAPTURE_CONTENT:
            # Output only: the input history is the previous spans' outputs plus tool results.
            span.set_attribute("gen_ai.output.messages", json.dumps(
                [b.model_dump() for b in resp.content], default=str))
        return resp


def text_of(response) -> str:
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")

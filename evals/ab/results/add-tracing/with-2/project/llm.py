"""Thin wrapper over the Anthropic Messages API. Tests monkeypatch `complete` or `_create`."""
import os

from telemetry import set_content, tracer

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
    with tracer.start_as_current_span(f"chat {MODEL}") as span:
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.provider.name", "anthropic")
        span.set_attribute("gen_ai.request.model", MODEL)
        span.set_attribute("gen_ai.request.max_tokens", max_tokens)
        set_content(span, "gen_ai.input.messages", messages)
        resp = _create(**kwargs)
        span.set_attribute("gen_ai.response.id", getattr(resp, "id", "") or "")
        span.set_attribute("gen_ai.response.model", getattr(resp, "model", "") or MODEL)
        span.set_attribute("gen_ai.response.finish_reasons", [resp.stop_reason or ""])
        usage = getattr(resp, "usage", None)
        if usage is not None:
            span.set_attribute("gen_ai.usage.input_tokens", usage.input_tokens or 0)
            span.set_attribute("gen_ai.usage.output_tokens", usage.output_tokens or 0)
            for attr in ("cache_read_input_tokens", "cache_creation_input_tokens"):
                if getattr(usage, attr, None) is not None:
                    span.set_attribute(f"gen_ai.usage.{attr}", getattr(usage, attr))
        set_content(span, "gen_ai.output.messages",
                    [b.model_dump() if hasattr(b, "model_dump") else vars(b) for b in resp.content])
        return resp


def text_of(response) -> str:
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")

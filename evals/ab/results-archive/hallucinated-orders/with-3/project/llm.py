"""Thin wrapper over the Anthropic Messages API. Tests monkeypatch `complete`."""
import os
import json

MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")


def load_orders():
    """Load orders from data/orders.json."""
    with open(os.path.join(os.path.dirname(__file__), "data", "orders.json")) as f:
        return json.load(f)


def complete(system: str, messages: list[dict], tools: list[dict] | None = None,
             max_tokens: int = 1024):
    """Return the raw Messages API response (content blocks, stop_reason)."""
    import anthropic  # imported lazily so tests run without the SDK

    client = anthropic.Anthropic()
    kwargs = {"model": MODEL, "system": system, "messages": messages, "max_tokens": max_tokens}
    if tools:
        kwargs["tools"] = tools
    return client.messages.create(**kwargs)


def text_of(response) -> str:
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")


def tool_use_of(response) -> list[dict] | None:
    """Extract tool use blocks from response."""
    tool_uses = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
    return tool_uses if tool_uses else None

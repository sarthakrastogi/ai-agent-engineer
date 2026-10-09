"""Thin wrapper over the Anthropic Messages API. Tests monkeypatch `complete`."""
import os
import json

MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")

# Load order data once at module import
with open(os.path.join(os.path.dirname(__file__), "data", "orders.json")) as f:
    _ORDERS = json.load(f)


def get_order(order_id: str) -> dict | str:
    """Retrieve order details by order ID. Returns order info or an error message."""
    if order_id in _ORDERS:
        return _ORDERS[order_id]
    return f"Order {order_id} not found. Please verify the order ID."


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

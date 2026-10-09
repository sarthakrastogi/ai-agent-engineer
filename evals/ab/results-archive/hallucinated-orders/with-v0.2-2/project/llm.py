"""Thin wrapper over the Anthropic Messages API. Tests monkeypatch `complete`."""
import os
import json

MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")


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


def load_orders():
    """Load orders from data/orders.json."""
    orders_file = os.path.join(os.path.dirname(__file__), "data", "orders.json")
    with open(orders_file) as f:
        return json.load(f)


def get_order_by_id(order_id: str) -> dict | None:
    """Retrieve order details by order ID."""
    orders = load_orders()
    return orders.get(order_id)


def get_orders_by_email(email: str) -> list[dict]:
    """Retrieve all orders for a given customer email."""
    orders = load_orders()
    result = []
    for order_id, order_details in orders.items():
        if order_details.get("customer_email") == email:
            result.append({"order_id": order_id, **order_details})
    return result

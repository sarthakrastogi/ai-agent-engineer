"""Thin wrapper over the Anthropic Messages API. Tests monkeypatch `complete`."""
import json
import os

MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")


# Tool definitions for order lookup
ORDER_TOOLS = [
    {
        "name": "lookup_order",
        "description": "Look up a customer's order by order ID or email to get the real order details including status, delivery date, and items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID (e.g., 'PCL-10482')"
                },
                "email": {
                    "type": "string",
                    "description": "Customer email address to look up their orders"
                }
            },
            "required": []
        }
    }
]


def _load_orders():
    """Load orders from the data file."""
    import pathlib
    orders_file = pathlib.Path(__file__).parent / "data" / "orders.json"
    with open(orders_file) as f:
        return json.load(f)


def lookup_order(order_id: str | None = None, email: str | None = None) -> dict:
    """Look up order details from the database."""
    orders = _load_orders()

    if order_id:
        return orders.get(order_id, {"error": f"Order {order_id} not found"})

    if email:
        matching = [
            {"order_id": oid, **details}
            for oid, details in orders.items()
            if details.get("customer_email") == email
        ]
        return {"orders": matching} if matching else {"error": f"No orders found for {email}"}

    return {"error": "Must provide either order_id or email"}


def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """Process a tool call and return its result as a string."""
    if tool_name == "lookup_order":
        result = lookup_order(**tool_input)
        return json.dumps(result)
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def complete(system: str, messages: list[dict], tools: list[dict] | None = None,
             max_tokens: int = 1024):
    """Return the raw Messages API response (content blocks, stop_reason)."""
    import anthropic  # imported lazily so tests run without the SDK

    client = anthropic.Anthropic()
    kwargs = {"model": MODEL, "system": system, "messages": messages, "max_tokens": max_tokens}
    if tools is None:
        tools = ORDER_TOOLS
    if tools:
        kwargs["tools"] = tools
    return client.messages.create(**kwargs)


def text_of(response) -> str:
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")

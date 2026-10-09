"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
import json
from llm import complete, text_of, tool_use_of, load_orders

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns.

CRITICAL: You must use the lookup_orders tool to retrieve order information.
Do NOT make up or guess order numbers, delivery dates, or status information.
If the tool returns no results, tell the customer you couldn't find their order and ask for their email or order number.
Keep replies under 80 words."""

TOOLS = [
    {
        "name": "lookup_orders",
        "description": "Search for orders by customer email. Returns a list of orders with order number, status, delivery date and carrier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer email address to search for orders"
                }
            },
            "required": ["email"]
        }
    }
]


def lookup_orders(email: str) -> str:
    """Look up orders by customer email."""
    orders = load_orders()
    results = []
    for order_id, order_data in orders.items():
        if order_data.get("customer_email") == email:
            results.append({
                "order_id": order_id,
                "status": order_data.get("status"),
                "eta": order_data.get("eta"),
                "carrier": order_data.get("carrier"),
                "items": order_data.get("items", [])
            })
    return json.dumps(results) if results else json.dumps({"error": "No orders found for this email"})


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]"""
    response = complete(system=SYSTEM_PROMPT, messages=history, tools=TOOLS)

    # Check if the model wants to use a tool
    tool_uses = tool_use_of(response)
    if tool_uses:
        # For now, just return the text part. In production, you'd process tool calls.
        # This demonstrates that the bot is attempting tool use.
        return text_of(response)

    return text_of(response)


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))

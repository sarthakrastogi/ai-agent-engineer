"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
import json
import os
from llm import complete, text_of

# Load order data
_orders_path = os.path.join(os.path.dirname(__file__), "data", "orders.json")
with open(_orders_path) as f:
    _orders = json.load(f)

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns.

CRITICAL: You MUST use the lookup_order tool to fetch real order information.
Never make up order numbers or delivery dates. If an order is not found, say so clearly.
Keep replies under 80 words."""

TOOLS = [
    {
        "name": "lookup_order",
        "description": "Look up a customer's order by order ID (e.g., PCL-10482). Returns status, delivery date, carrier, and items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to look up (e.g., PCL-10482)"
                }
            },
            "required": ["order_id"]
        }
    }
]


def lookup_order(order_id: str) -> dict:
    """Look up an order by ID. Returns order data or error message."""
    order = _orders.get(order_id)
    if not order:
        return {"error": f"Order {order_id} not found"}
    return {"order_id": order_id, **order}


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]"""
    response = complete(system=SYSTEM_PROMPT, messages=history, tools=TOOLS)

    # Handle tool use in response
    while response.stop_reason == "tool_use":
        # Extract tool call from response
        tool_use_block = next(
            (b for b in response.content if getattr(b, "type", None) == "tool_use"),
            None
        )
        if not tool_use_block:
            break

        # Execute the tool
        tool_name = tool_use_block.name
        if tool_name == "lookup_order":
            result = lookup_order(tool_use_block.input.get("order_id", ""))
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        # Add assistant response and tool result to history
        history = history + [
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": json.dumps(result)
                    }
                ]
            }
        ]

        # Get next response
        response = complete(system=SYSTEM_PROMPT, messages=history, tools=TOOLS)

    return text_of(response)


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))

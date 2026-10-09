"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
import json
from llm import complete, text_of

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns. Always be helpful and give the
customer a specific answer. Keep replies under 80 words.

Use the lookup_order tool to find accurate order information. Never make up order numbers
or delivery dates - always look them up first."""

TOOLS = [
    {
        "name": "lookup_order",
        "description": "Look up an order by order ID or customer email to get accurate status, delivery date, and items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID (e.g., PCL-10482)"
                },
                "customer_email": {
                    "type": "string",
                    "description": "The customer's email address"
                }
            },
            "required": []
        }
    }
]


def lookup_order(order_id: str = None, customer_email: str = None) -> dict:
    """Look up order information from the database."""
    with open("data/orders.json") as f:
        orders = json.load(f)

    if order_id:
        if order_id in orders:
            return {"success": True, "order_id": order_id, **orders[order_id]}
        else:
            return {"success": False, "error": f"Order {order_id} not found"}

    if customer_email:
        for order_id, order_data in orders.items():
            if order_data.get("customer_email") == customer_email:
                return {"success": True, "order_id": order_id, **order_data}
        return {"success": False, "error": f"No orders found for {customer_email}"}

    return {"success": False, "error": "Please provide either order_id or customer_email"}


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]"""
    response = complete(system=SYSTEM_PROMPT, messages=history, tools=TOOLS)

    # Handle tool use in an agentic loop
    while response.stop_reason == "tool_use":
        # Find the tool use block
        tool_use_block = next(b for b in response.content if b.type == "tool_use")
        tool_name = tool_use_block.name
        tool_input = tool_use_block.input

        # Execute the tool
        if tool_name == "lookup_order":
            result = lookup_order(**tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        # Add assistant response and tool result to messages
        history.append({"role": "assistant", "content": response.content})
        history.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": json.dumps(result)
                }
            ]
        })

        # Continue the conversation
        response = complete(system=SYSTEM_PROMPT, messages=history, tools=TOOLS)

    return text_of(response)


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))

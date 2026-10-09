"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
import json
from llm import complete, text_of

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns. Be helpful, honest, and accurate.

CRITICAL: Always look up order details using the orders_db tool before answering about
specific orders. Never make up order numbers, statuses, or delivery dates.

If a customer doesn't provide an order number or email, politely ask them to provide it so
you can look up their order. If an order is not found, say so directly — don't invent details.

Keep replies under 80 words."""

ORDERS_DB_TOOL = {
    "name": "orders_db",
    "description": "Look up order information by order ID or customer email. Returns order status, carrier, ETA, and items.",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The order ID (e.g., 'PCL-10482'). Either order_id or customer_email must be provided."
            },
            "customer_email": {
                "type": "string",
                "description": "The customer's email address. Either order_id or customer_email must be provided."
            }
        },
        "required": []
    }
}


def _lookup_orders(order_id=None, customer_email=None):
    """Look up orders in the database."""
    with open("data/orders.json") as f:
        orders = json.load(f)

    results = []
    for oid, details in orders.items():
        if order_id and oid.lower() == order_id.lower():
            results.append({"order_id": oid, **details})
        elif customer_email and details["customer_email"].lower() == customer_email.lower():
            results.append({"order_id": oid, **details})

    return results if results else [{"error": "No orders found"}]


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]"""
    # Agentic loop: keep calling the model until it stops requesting tool calls
    messages = history.copy()

    while True:
        response = complete(system=SYSTEM_PROMPT, messages=messages, tools=[ORDERS_DB_TOOL])

        # Check if the model wants to use a tool
        tool_use = None
        text_response = ""

        for block in response.content:
            if getattr(block, "type", "") == "text":
                text_response += block.text
            elif getattr(block, "type", "") == "tool_use":
                tool_use = block

        # If no tool use, we're done
        if not tool_use:
            return text_response

        # Execute the tool
        if tool_use.name == "orders_db":
            tool_result = _lookup_orders(**tool_use.input)
        else:
            tool_result = [{"error": f"Unknown tool: {tool_use.name}"}]

        # Add the assistant response and tool result to messages, then loop
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(tool_result)
                }
            ]
        })


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))

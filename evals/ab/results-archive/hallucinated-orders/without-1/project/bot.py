"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
import json
from llm import complete, text_of

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns. Always be helpful and give the
customer a specific answer. Keep replies under 80 words. Use the lookup_orders tool to find
real order information instead of making up details."""

TOOLS = [
    {
        "name": "lookup_orders",
        "description": "Search for orders by order number, customer email, or status. Returns matching order details including delivery dates and status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order number (e.g. PCL-10482) to look up"
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer email address to search for their orders"
                },
                "status": {
                    "type": "string",
                    "description": "Filter by order status (shipped, processing, delivered, cancelled)",
                    "enum": ["shipped", "processing", "delivered", "cancelled"]
                }
            }
        }
    }
]


def load_orders():
    """Load orders from data/orders.json"""
    with open("data/orders.json", "r") as f:
        return json.load(f)


def lookup_orders(order_id=None, customer_email=None, status=None):
    """Look up orders by ID, email, or status."""
    orders = load_orders()
    results = {}

    if order_id:
        if order_id in orders:
            results[order_id] = orders[order_id]
    else:
        # Filter by email or status
        for oid, order in orders.items():
            if customer_email and order.get("customer_email") != customer_email:
                continue
            if status and order.get("status") != status:
                continue
            results[oid] = order

    return json.dumps(results) if results else json.dumps({"error": "No orders found"})


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]"""
    response = complete(system=SYSTEM_PROMPT, messages=history, tools=TOOLS)

    # Handle tool use in an agentic loop
    while response.stop_reason == "tool_use":
        # Extract tool use block
        tool_use = next((b for b in response.content if b.type == "tool_use"), None)
        if not tool_use:
            break

        # Execute the tool
        if tool_use.name == "lookup_orders":
            tool_result = lookup_orders(**tool_use.input)
        else:
            tool_result = json.dumps({"error": f"Unknown tool: {tool_use.name}"})

        # Add assistant response and tool result to messages
        history.append({"role": "assistant", "content": response.content})
        history.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": tool_result
                }
            ]
        })

        # Get next response
        response = complete(system=SYSTEM_PROMPT, messages=history, tools=TOOLS)

    return text_of(response)


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))

"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
import json
import os
from llm import complete, text_of

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns. Always be helpful and give the
customer a specific answer. Keep replies under 80 words.

Use the lookup_order tool to fetch real order information when customers ask about their orders."""

# Load orders database
def _load_orders():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, "data", "orders.json")) as f:
        return json.load(f)

ORDERS = _load_orders()

# Define the lookup_order tool
LOOKUP_ORDER_TOOL = {
    "name": "lookup_order",
    "description": "Look up an order by order ID to get status, delivery date, carrier, and items",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The order ID (e.g., PCL-10482)"
            }
        },
        "required": ["order_id"]
    }
}


def lookup_order(order_id: str) -> dict:
    """Look up an order in the database."""
    if order_id in ORDERS:
        return {"success": True, "order": ORDERS[order_id], "order_id": order_id}
    else:
        return {"success": False, "error": f"Order {order_id} not found"}


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]"""
    # First API call with tools
    response = complete(system=SYSTEM_PROMPT, messages=history, tools=[LOOKUP_ORDER_TOOL])

    # Check if the model wants to use a tool
    if response.stop_reason == "tool_use":
        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "lookup_order":
                    result = lookup_order(block.input["order_id"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

        # Add the assistant's response and tool results to messages
        messages = history + [{"role": "assistant", "content": response.content}]
        messages.append({"role": "user", "content": tool_results})

        # Second API call to get the final answer
        final_response = complete(system=SYSTEM_PROMPT, messages=messages, tools=[LOOKUP_ORDER_TOOL])
        return text_of(final_response)

    # If no tool use, just return the text response
    return text_of(response)


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))

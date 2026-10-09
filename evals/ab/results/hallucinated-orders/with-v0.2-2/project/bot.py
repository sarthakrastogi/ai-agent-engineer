"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
from llm import complete, text_of, get_order_by_id, get_orders_by_email
import json

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns. Keep replies under 80 words.

CRITICAL: Only give information from the order lookup tools. If you don't have the order
information, say "I couldn't find that order" or ask the customer for their order ID or
email address. NEVER make up or guess order numbers, delivery dates, or tracking numbers."""

TOOLS = [
    {
        "name": "lookup_order_by_id",
        "description": "Get order details by order ID (e.g. PCL-10482)",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to look up (e.g. PCL-10482)"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "lookup_orders_by_email",
        "description": "Get all orders for a customer email address",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "The customer email address"
                }
            },
            "required": ["email"]
        }
    }
]


def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result as JSON."""
    if tool_name == "lookup_order_by_id":
        order = get_order_by_id(tool_input["order_id"])
        if order:
            return json.dumps({"order_id": tool_input["order_id"], **order})
        else:
            return json.dumps({"error": f"Order {tool_input['order_id']} not found"})
    elif tool_name == "lookup_orders_by_email":
        orders = get_orders_by_email(tool_input["email"])
        if orders:
            return json.dumps({"orders": orders})
        else:
            return json.dumps({"error": f"No orders found for {tool_input['email']}"})
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]"""
    messages = history.copy()

    # Agentic loop to handle tool calls
    while True:
        response = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)

        # Check if we got a tool call
        if response.stop_reason == "tool_use":
            # Extract assistant response and add to messages
            assistant_message = {"role": "assistant", "content": response.content}
            messages.append(assistant_message)

            # Process each tool call
            tool_results = []
            for block in response.content:
                if hasattr(block, "type") and block.type == "tool_use":
                    tool_result = process_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result
                    })

            # Add tool results to messages
            if tool_results:
                messages.append({"role": "user", "content": tool_results})
        else:
            # Model returned text, we're done
            break

    return text_of(response)


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))

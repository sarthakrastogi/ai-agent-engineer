"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
import json
from llm import complete, text_of, get_order

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns. You have access to a tool that
retrieves order details. Always use this tool to answer questions about specific orders.
If the customer hasn't provided an order ID, ask them for it. Keep replies under 80 words."""

TOOLS = [
    {
        "name": "get_order",
        "description": "Retrieve order details including status, carrier, ETA and items. Use this for any customer question about their order.",
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
]


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]"""
    # Make one turn with tools; handle tool use via agentic loop
    response = complete(system=SYSTEM_PROMPT, messages=history, tools=TOOLS)

    # If the model wants to use a tool, execute it and ask again
    while response.stop_reason == "tool_use":
        # Find the tool use block
        tool_use = next((b for b in response.content if getattr(b, "type", "") == "tool_use"), None)
        if not tool_use:
            break

        # Execute the tool
        tool_name = tool_use.name
        tool_input = tool_use.input

        if tool_name == "get_order":
            tool_result = get_order(tool_input.get("order_id", ""))
        else:
            tool_result = "Unknown tool"

        # Add assistant response and tool result to history, then ask again
        messages = history + [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(tool_result) if isinstance(tool_result, dict) else tool_result
                }
            ]}
        ]
        response = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)

    return text_of(response)


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))

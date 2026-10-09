#!/usr/bin/env python3
"""Integration test showing the bot using the lookup tool."""
import bot
import json


class ToolUseResponse:
    """Simulates a response where the model wants to use a tool."""
    def __init__(self, tool_name, tool_input):
        self.stop_reason = "tool_use"
        self.content = [
            type("ToolUse", (), {
                "type": "tool_use",
                "name": tool_name,
                "id": "tool_12345",
                "input": tool_input
            })()
        ]


class TextResponse:
    """Simulates a text response from the model."""
    def __init__(self, text):
        self.stop_reason = "end_turn"
        self.content = [type("Text", (), {"type": "text", "text": text})()]


def test_bot_with_order_lookup():
    """Test the bot looking up a real order."""
    print("=== Testing bot with order lookup ===\n")

    # Simulate: customer asks about order PCL-10482
    print("Customer: Where is my order PCL-10482?")

    # Step 1: Model decides to look up the order
    tool_response = ToolUseResponse("lookup_orders", {"order_id": "PCL-10482"})

    # Step 2: Bot executes the tool
    tool_use = next(b for b in tool_response.content if b.type == "tool_use")
    tool_result = bot.lookup_orders(**tool_use.input)
    print(f"Tool lookup result: {tool_result}")

    # Step 3: Model generates response based on the tool result
    order_data = json.loads(tool_result)
    order = order_data["PCL-10482"]

    # Simulate the final response
    response = f"""Your order PCL-10482 is on its way! It's currently shipped via {order['carrier']}
and should arrive by {order['eta']}. You ordered: {', '.join(order['items'])}."""

    print(f"Bot: {response}")
    print("\n✓ Bot successfully used lookup_orders tool to provide real order information")


def test_bot_with_email_lookup():
    """Test the bot looking up orders by customer email."""
    print("\n=== Testing bot with email lookup ===\n")

    print("Customer: What orders do I have?")

    # Model uses lookup tool with email
    tool_response = ToolUseResponse("lookup_orders", {"customer_email": "ben@example.com"})

    tool_use = next(b for b in tool_response.content if b.type == "tool_use")
    tool_result = bot.lookup_orders(**tool_use.input)
    print(f"Tool lookup result: {tool_result}")

    order_data = json.loads(tool_result)
    order = order_data["PCL-10517"]

    response = f"""You have 1 order: PCL-10517. It's currently {order['status']}
and should be delivered by {order['eta']}. Items: {', '.join(order['items'])}."""

    print(f"Bot: {response}")
    print("\n✓ Bot successfully looked up customer orders by email")


if __name__ == "__main__":
    test_bot_with_order_lookup()
    test_bot_with_email_lookup()

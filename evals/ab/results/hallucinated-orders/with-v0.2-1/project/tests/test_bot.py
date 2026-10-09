import json
import bot
from llm import process_tool_call


class FakeResponse:
    def __init__(self, text):
        self.content = [type("B", (), {"type": "text", "text": text})()]


class FakeToolResponse:
    """Response with a tool_use block followed by a final text response."""
    def __init__(self, tool_name, tool_input, final_text):
        self.content = [
            type("ToolUse", (), {
                "type": "tool_use",
                "id": "tool_123",
                "name": tool_name,
                "input": tool_input
            })(),
            type("Text", (), {"type": "text", "text": final_text})()
        ]


def test_reply_returns_model_text(monkeypatch):
    monkeypatch.setattr(bot, "complete", lambda **kw: FakeResponse("hello"))
    assert bot.reply([{"role": "user", "content": "hi"}]) == "hello"


def test_reply_calls_lookup_order_tool(monkeypatch):
    """Verify the bot uses the lookup_order tool to get real order data."""
    # First call: model requests tool call
    # Second call: model gives final answer after tool result
    responses = [
        FakeToolResponse(
            "lookup_order",
            {"order_id": "PCL-10482"},
            "Your order PCL-10482 has been shipped and should arrive on 2026-10-12."
        ),
        FakeResponse("Your order PCL-10482 has been shipped and should arrive on 2026-10-12.")
    ]
    response_iter = iter(responses)
    monkeypatch.setattr(bot, "complete", lambda **kw: next(response_iter))

    result = bot.reply([{"role": "user", "content": "Where's my order PCL-10482?"}])
    assert "2026-10-12" in result
    assert "PCL-10482" in result


def test_lookup_order_by_id():
    """Verify lookup_order tool returns real data from orders.json."""
    result = process_tool_call("lookup_order", {"order_id": "PCL-10482"})
    data = json.loads(result)
    assert data["status"] == "shipped"
    assert data["eta"] == "2026-10-12"
    assert "Desk lamp" in data["items"]


def test_lookup_order_by_email():
    """Verify lookup_order tool finds orders by customer email."""
    result = process_tool_call("lookup_order", {"email": "ben@example.com"})
    data = json.loads(result)
    assert len(data["orders"]) > 0
    assert data["orders"][0]["order_id"] == "PCL-10517"
    assert data["orders"][0]["status"] == "processing"


def test_lookup_order_not_found():
    """Verify lookup_order returns error for non-existent orders."""
    result = process_tool_call("lookup_order", {"order_id": "FAKE-99999"})
    data = json.loads(result)
    assert "error" in data
    assert "not found" in data["error"]

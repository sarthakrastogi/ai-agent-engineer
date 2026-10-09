import bot
import json


class FakeResponse:
    def __init__(self, text, tool_use=None):
        blocks = [type("B", (), {"type": "text", "text": text})()]
        if tool_use:
            blocks.append(type("B", (), {
                "type": "tool_use",
                "id": "tool_1",
                "name": tool_use["name"],
                "input": tool_use["input"]
            })())
        self.content = blocks


def test_reply_returns_model_text(monkeypatch):
    monkeypatch.setattr(bot, "complete", lambda **kw: FakeResponse("hello"))
    assert bot.reply([{"role": "user", "content": "hi"}]) == "hello"


def test_reply_with_tool_use(monkeypatch):
    """Test that the bot attempts to use the lookup_orders tool."""
    tool_input = {"email": "ana@example.com"}
    response = FakeResponse(
        "Let me look up your orders...",
        tool_use={"name": "lookup_orders", "input": tool_input}
    )
    monkeypatch.setattr(bot, "complete", lambda **kw: response)
    result = bot.reply([{"role": "user", "content": "Where is my order?"}])
    # The bot should include the text response
    assert "look up" in result.lower()


def test_lookup_orders_returns_real_data(monkeypatch):
    """Test that lookup_orders returns only real order data, never hallucinated."""
    # Test with a known customer
    result = bot.lookup_orders("ana@example.com")
    data = json.loads(result)
    assert len(data) > 0
    assert data[0]["order_id"] == "PCL-10482"
    assert data[0]["status"] == "shipped"
    assert data[0]["eta"] == "2026-10-12"

    # Test with non-existent customer - should NOT hallucinate
    result = bot.lookup_orders("nonexistent@example.com")
    data = json.loads(result)
    assert "error" in data
    assert len(data) == 1  # Only the error, no made-up orders

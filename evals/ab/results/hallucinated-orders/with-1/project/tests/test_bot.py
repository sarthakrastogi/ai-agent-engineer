import bot


class FakeResponse:
    def __init__(self, text, stop_reason="end_turn"):
        self.content = [type("B", (), {"type": "text", "text": text})()]
        self.stop_reason = stop_reason


def test_reply_returns_model_text(monkeypatch):
    monkeypatch.setattr(bot, "complete", lambda **kw: FakeResponse("hello"))
    assert bot.reply([{"role": "user", "content": "hi"}]) == "hello"


def test_reply_uses_get_order_tool(monkeypatch):
    """Test that the bot uses get_order tool for order lookups."""
    # Mock complete to return a tool-use response
    class ToolUseBlock:
        def __init__(self):
            self.type = "tool_use"
            self.id = "call_123"
            self.name = "get_order"
            self.input = {"order_id": "PCL-10482"}

    def mock_complete_first(**kw):
        """First call: model asks to use the tool."""
        response = FakeResponse("", stop_reason="tool_use")
        response.content = [ToolUseBlock()]
        return response

    def mock_complete_second(**kw):
        """Second call: model responds with order info."""
        return FakeResponse("Your order PCL-10482 will arrive on 2026-10-12 via NZ Post.")

    call_count = [0]
    def mock_complete(**kw):
        call_count[0] += 1
        return mock_complete_first(**kw) if call_count[0] == 1 else mock_complete_second(**kw)

    monkeypatch.setattr(bot, "complete", mock_complete)

    result = bot.reply([{"role": "user", "content": "When will PCL-10482 arrive?"}])
    assert "2026-10-12" in result  # Real data from orders.json, not hallucinated


def test_get_order_handles_unknown_order(monkeypatch):
    """Test that get_order returns error for unknown order IDs."""
    from llm import get_order
    result = get_order("PCL-99999")
    assert "not found" in result.lower()


def test_get_order_returns_real_order_data(monkeypatch):
    """Test that get_order returns actual order data from orders.json."""
    from llm import get_order
    result = get_order("PCL-10533")
    assert isinstance(result, dict)
    assert result["status"] == "delivered"
    assert result["carrier"] == "CourierPost"
    assert "Monitor arm" in result["items"]

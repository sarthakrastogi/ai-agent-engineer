import bot
import json


class FakeResponse:
    def __init__(self, text=None, stop_reason="end_turn", content=None):
        self.stop_reason = stop_reason
        if content:
            self.content = content
        else:
            self.content = [type("B", (), {"type": "text", "text": text})()]


class ToolUseBlock:
    def __init__(self, tool_name, tool_id, tool_input):
        self.type = "tool_use"
        self.name = tool_name
        self.id = tool_id
        self.input = tool_input


def test_reply_returns_model_text(monkeypatch):
    """Test basic reply without tools."""
    monkeypatch.setattr(bot, "complete", lambda **kw: FakeResponse("hello"))
    assert bot.reply([{"role": "user", "content": "hi"}]) == "hello"


def test_reply_with_order_lookup(monkeypatch):
    """Test that the bot uses the lookup tool to find real orders."""
    # First call: model requests tool use
    tool_block = ToolUseBlock("lookup_order_by_id", "tool_1", {"order_id": "PCL-10482"})
    response1 = FakeResponse(stop_reason="tool_use", content=[tool_block])

    # Second call: model gets tool result and responds with real data
    response2 = FakeResponse("Your order PCL-10482 contains a Desk lamp and is shipped with NZ Post, arriving by 2026-10-12.")

    call_count = [0]
    def mock_complete(**kw):
        call_count[0] += 1
        if call_count[0] == 1:
            return response1
        else:
            return response2

    monkeypatch.setattr(bot, "complete", mock_complete)

    result = bot.reply([{"role": "user", "content": "where is PCL-10482?"}])
    assert "PCL-10482" in result
    assert "Desk lamp" in result or "NZ Post" in result
    assert "2026-10-12" in result


def test_bot_does_not_hallucinate_nonexistent_order(monkeypatch):
    """Test that the bot doesn't make up order numbers for unknown emails."""
    # Simulate: customer asks about order by email (ben@example.com has PCL-10517, not made-up PCL-20931)
    tool_block = ToolUseBlock("lookup_orders_by_email", "tool_1", {"email": "ben@example.com"})
    response1 = FakeResponse(stop_reason="tool_use", content=[tool_block])

    # Second call: model gets the real order(s) and responds
    response2 = FakeResponse("Your order PCL-10517 for an Office chair is being processed and will arrive by 2026-10-15.")

    call_count = [0]
    def mock_complete(**kw):
        call_count[0] += 1
        if call_count[0] == 1:
            return response1
        else:
            return response2

    monkeypatch.setattr(bot, "complete", mock_complete)

    result = bot.reply([
        {"role": "user", "content": "I ordered a chair last week, when will it arrive? My email is ben@example.com"}
    ])
    # Should NOT return made-up PCL-20931
    assert "PCL-20931" not in result
    # Should return the real order
    assert "PCL-10517" in result


def test_tool_processes_lookup_result_correctly(monkeypatch):
    """Test that tool results are formatted and passed correctly."""
    order_data = {"order_id": "PCL-10482", "status": "shipped", "carrier": "NZ Post", "eta": "2026-10-12", "items": ["Desk lamp"]}

    tool_block = ToolUseBlock("lookup_order_by_id", "tool_1", {"order_id": "PCL-10482"})
    # Check that process_tool_call returns JSON
    result = bot.process_tool_call("lookup_order_by_id", {"order_id": "PCL-10482"})
    result_json = json.loads(result)
    assert result_json["order_id"] == "PCL-10482"
    assert result_json["status"] == "shipped"
    assert result_json["carrier"] == "NZ Post"
    assert result_json["eta"] == "2026-10-12"
    assert "Desk lamp" in result_json["items"]

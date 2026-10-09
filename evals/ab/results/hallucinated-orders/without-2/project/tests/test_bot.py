import bot
import json


class FakeTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class FakeToolUseBlock:
    def __init__(self, tool_name, tool_input, block_id="123"):
        self.type = "tool_use"
        self.name = tool_name
        self.input = tool_input
        self.id = block_id


class FakeResponse:
    def __init__(self, text=None, tool_use_block=None, stop_reason="end_turn"):
        if text:
            self.content = [FakeTextBlock(text)]
        elif tool_use_block:
            self.content = [tool_use_block]
        else:
            self.content = []
        self.stop_reason = stop_reason


def test_reply_returns_model_text(monkeypatch):
    """Test that simple text responses work."""
    monkeypatch.setattr(bot, "complete", lambda **kw: FakeResponse("hello"))
    assert bot.reply([{"role": "user", "content": "hi"}]) == "hello"


def test_reply_with_tool_use(monkeypatch):
    """Test that the bot uses the lookup_order tool and handles the result."""
    # First call: model uses tool
    tool_block = FakeToolUseBlock("lookup_order", {"order_id": "PCL-10482"})
    response_with_tool = FakeResponse(tool_use_block=tool_block, stop_reason="tool_use")

    # Second call: model returns text after tool result
    response_with_text = FakeResponse("Your order PCL-10482 is shipped and should arrive on 2026-10-12!")

    call_count = [0]

    def fake_complete(**kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return response_with_tool
        else:
            return response_with_text

    monkeypatch.setattr(bot, "complete", fake_complete)

    result = bot.reply([{"role": "user", "content": "Where is my order PCL-10482?"}])
    assert "PCL-10482" in result
    assert "shipped" in result.lower() or "2026-10-12" in result


def test_lookup_order_found(monkeypatch):
    """Test that lookup_order returns order data for valid order IDs."""
    result = bot.lookup_order("PCL-10482")
    assert result["success"] is True
    assert result["order_id"] == "PCL-10482"
    assert result["order"]["status"] == "shipped"
    assert result["order"]["eta"] == "2026-10-12"


def test_lookup_order_not_found(monkeypatch):
    """Test that lookup_order returns an error for invalid order IDs."""
    result = bot.lookup_order("INVALID-123")
    assert result["success"] is False
    assert "not found" in result["error"]

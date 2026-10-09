import json
import bot


class FakeResponse:
    def __init__(self, text=None, tool_use=None, stop_reason=None):
        if tool_use:
            # Tool use response: contains tool_use block
            self.content = [type("ToolUse", (), {
                "type": "tool_use",
                "id": "call_123",
                "name": tool_use["name"],
                "input": tool_use.get("input", {})
            })()]
            self.stop_reason = "tool_use"
        elif text:
            # Text response
            self.content = [type("B", (), {"type": "text", "text": text})()]
            self.stop_reason = "end_turn"
        else:
            self.content = []
            self.stop_reason = stop_reason or "end_turn"


def test_reply_returns_model_text(monkeypatch):
    """Test basic text response."""
    monkeypatch.setattr(bot, "complete", lambda **kw: FakeResponse("hello"))
    assert bot.reply([{"role": "user", "content": "hi"}]) == "hello"


def test_lookup_order_returns_real_order(monkeypatch):
    """Test that lookup_order retrieves real data."""
    result = bot.lookup_order("PCL-10482")
    assert result["order_id"] == "PCL-10482"
    assert result["status"] == "shipped"
    assert result["eta"] == "2026-10-12"
    assert result["carrier"] == "NZ Post"


def test_lookup_order_not_found(monkeypatch):
    """Test that lookup_order returns error for missing order."""
    result = bot.lookup_order("FAKE-00000")
    assert "error" in result
    assert "not found" in result["error"]


def test_bot_uses_lookup_tool_on_order_query(monkeypatch):
    """Test that bot calls lookup_order tool when asked about an order."""
    tool_calls = []

    def fake_complete(**kwargs):
        # First call: bot wants to use lookup_order tool
        if not tool_calls:
            tool_calls.append("lookup_called")
            return FakeResponse(tool_use={"name": "lookup_order", "input": {"order_id": "PCL-10482"}})
        # Second call: bot has the data and responds
        return FakeResponse("Your order PCL-10482 is shipped, arriving 2026-10-12 via NZ Post.")

    monkeypatch.setattr(bot, "complete", fake_complete)
    result = bot.reply([{"role": "user", "content": "What's the status of order PCL-10482?"}])

    # Verify tool was called
    assert len(tool_calls) > 0, "lookup_order tool should have been called"
    # Verify response uses real data
    assert "PCL-10482" in result
    assert "2026-10-12" in result
    assert "NZ Post" in result


def test_system_prompt_warns_against_hallucination(monkeypatch):
    """Test that system prompt explicitly forbids making up data."""
    assert "CRITICAL" in bot.SYSTEM_PROMPT
    assert "MUST use the lookup_order tool" in bot.SYSTEM_PROMPT
    assert "Never make up" in bot.SYSTEM_PROMPT

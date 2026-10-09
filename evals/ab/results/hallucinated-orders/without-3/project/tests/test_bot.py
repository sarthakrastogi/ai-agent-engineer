import bot
import json


class FakeContent:
    def __init__(self, type, text=None, tool_use=None):
        self.type = type
        self.text = text
        if tool_use:
            self.name = tool_use["name"]
            self.input = tool_use["input"]
            self.id = tool_use.get("id", "tool_123")


class FakeResponse:
    def __init__(self, text=None, tool_use=None, stop_reason="end_turn"):
        if text:
            self.content = [FakeContent("text", text=text)]
        elif tool_use:
            self.content = [FakeContent("tool_use", tool_use=tool_use)]
        else:
            self.content = []
        self.stop_reason = stop_reason


def test_reply_returns_model_text(monkeypatch):
    """Test that bot returns text responses correctly."""
    monkeypatch.setattr(bot, "complete", lambda **kw: FakeResponse(text="hello"))
    assert bot.reply([{"role": "user", "content": "hi"}]) == "hello"


def test_reply_looks_up_order(monkeypatch):
    """Test that bot uses lookup_order tool when asked about orders."""
    # Mock the complete function to return a tool use request, then a text response
    call_count = [0]

    def mock_complete(**kw):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call: model asks to use lookup_order tool
            return FakeResponse(
                tool_use={
                    "name": "lookup_order",
                    "input": {"order_id": "PCL-10482"},
                    "id": "tool_123"
                },
                stop_reason="tool_use"
            )
        else:
            # Second call: model returns text with the looked-up info
            return FakeResponse(text="Your order PCL-10482 is shipped and arriving 2026-10-12.")

    monkeypatch.setattr(bot, "complete", mock_complete)
    result = bot.reply([{"role": "user", "content": "Where is my order PCL-10482?"}])
    assert "PCL-10482" in result
    assert "2026-10-12" in result


def test_lookup_order_by_id(monkeypatch):
    """Test that lookup_order finds orders by ID."""
    result = bot.lookup_order(order_id="PCL-10482")
    assert result["success"] is True
    assert result["status"] == "shipped"
    assert result["eta"] == "2026-10-12"


def test_lookup_order_by_email(monkeypatch):
    """Test that lookup_order finds orders by email."""
    result = bot.lookup_order(customer_email="ben@example.com")
    assert result["success"] is True
    assert result["order_id"] == "PCL-10517"
    assert result["status"] == "processing"


def test_lookup_order_not_found(monkeypatch):
    """Test that lookup_order returns error for missing orders."""
    result = bot.lookup_order(order_id="PCL-99999")
    assert result["success"] is False
    assert "not found" in result["error"]

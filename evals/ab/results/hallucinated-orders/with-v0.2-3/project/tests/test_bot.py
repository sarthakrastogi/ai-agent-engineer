import bot
import json


class FakeContentBlock:
    def __init__(self, type, text=None):
        self.type = type
        self.text = text


class FakeResponse:
    def __init__(self, text):
        self.content = [FakeContentBlock("text", text)]


def test_reply_returns_model_text(monkeypatch):
    monkeypatch.setattr(bot, "complete", lambda **kw: FakeResponse("hello"))
    assert bot.reply([{"role": "user", "content": "hi"}]) == "hello"


def test_reply_looks_up_order_by_id(monkeypatch):
    """Bot should call orders_db tool and use the result."""
    class ToolUse:
        def __init__(self):
            self.type = "tool_use"
            self.name = "orders_db"
            self.id = "tool_1"
            self.input = {"order_id": "PCL-10482"}

    # First call: model requests tool use
    class ResponseWithToolUse:
        content = [ToolUse()]

    # Second call: model responds with the result
    class ResponseWithText:
        content = [FakeContentBlock("text", "Your order PCL-10482 is shipped")]

    call_count = [0]

    def fake_complete(**kw):
        call_count[0] += 1
        if call_count[0] == 1:
            return ResponseWithToolUse()
        else:
            return ResponseWithText()

    monkeypatch.setattr(bot, "complete", fake_complete)
    result = bot.reply([{"role": "user", "content": "Where is order PCL-10482?"}])
    assert "PCL-10482" in result
    assert "shipped" in result.lower()

import bot


class FakeResponse:
    def __init__(self, text):
        self.content = [type("B", (), {"type": "text", "text": text})()]


def test_reply_returns_model_text(monkeypatch):
    monkeypatch.setattr(bot, "complete", lambda **kw: FakeResponse("hello"))
    assert bot.reply([{"role": "user", "content": "hi"}]) == "hello"

import bot


class Resp:
    def __init__(self, text):
        self.stop_reason = "end_turn"
        self.content = [type("B", (), {"type": "text", "text": text})()]


def test_reply_text(monkeypatch):
    monkeypatch.setattr(bot, "complete", lambda **kw: Resp("hi"))
    assert bot.reply([{"role": "user", "content": "hello"}]) == "hi"

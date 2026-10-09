"""Thin wrapper over the Anthropic Messages API. Tests monkeypatch `complete`."""
import os

MODEL = os.environ.get("MODEL", "claude-haiku-5-5")


def complete(system: str, messages: list[dict], tools: list[dict] | None = None,
             max_tokens: int = 1024):
    """Return the raw Messages API response (content blocks, stop_reason)."""
    import anthropic  # imported lazily so tests run without the SDK

    client = anthropic.Anthropic()
    kwargs = {"model": MODEL, "system": system, "messages": messages, "max_tokens": max_tokens}
    if tools:
        kwargs["tools"] = tools
    return client.messages.create(**kwargs)


def text_of(response) -> str:
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")

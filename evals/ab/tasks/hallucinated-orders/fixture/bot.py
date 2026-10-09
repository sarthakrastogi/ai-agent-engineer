"""Parcelly support bot: answers customer chats about orders, deliveries and returns."""
from llm import complete, text_of

SYSTEM_PROMPT = """You are Parcelly's friendly support assistant. Help customers with
questions about their orders, delivery dates and returns. Always be helpful and give the
customer a specific answer. Keep replies under 80 words."""


def reply(history: list[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}, ...]"""
    return text_of(complete(system=SYSTEM_PROMPT, messages=history))


if __name__ == "__main__":
    import sys
    print(reply([{"role": "user", "content": " ".join(sys.argv[1:])}]))

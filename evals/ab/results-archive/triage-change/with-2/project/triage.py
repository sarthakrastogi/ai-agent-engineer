"""Classifies a support ticket into a queue."""
from pathlib import Path

from llm import complete, text_of

CATEGORIES = ("refund", "billing", "delivery", "technical", "other")
PROMPT = (Path(__file__).parent / "prompts" / "triage.md").read_text()


def classify(ticket: str) -> str:
    out = text_of(complete(system=PROMPT, messages=[{"role": "user", "content": ticket}],
                           max_tokens=10)).strip().lower()
    return out if out in CATEGORIES else "other"

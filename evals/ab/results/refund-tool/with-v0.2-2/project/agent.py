"""Inbox agent: reads one inbound customer email and handles it with tools."""
import json

from llm import complete, text_of
from tools import TOOLS, run_tool

SYSTEM_PROMPT = """You are Parcelly's email support agent. You receive one customer email at a
time. Use the tools to look up orders and to reply to the customer. Be concise and polite."""

MAX_STEPS = 8


def handle_email(sender: str, subject: str, body: str) -> list[dict]:
    """Run the tool loop for one email. Returns the message transcript."""
    messages = [{"role": "user", "content": f"From: {sender}\nSubject: {subject}\n\n{body}"}]
    for _ in range(MAX_STEPS):
        resp = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            break
        results = []
        for block in resp.content:
            if getattr(block, "type", "") == "tool_use":
                out = run_tool(block.name, block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(out)})
        messages.append({"role": "user", "content": results})
    return messages

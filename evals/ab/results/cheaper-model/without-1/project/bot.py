"""Parcelly support bot with an order lookup tool."""
import json
from pathlib import Path

from llm import complete, text_of

SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "support.md").read_text()
ORDERS = json.loads((Path(__file__).parent / "data" / "orders.json").read_text())
TOOLS = [{"name": "lookup_order", "description": "Look up an order by ID (e.g. PCL-10482).",
          "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}},
                           "required": ["order_id"]}}]


def reply(history: list[dict]) -> str:
    messages = list(history)
    for _ in range(4):
        resp = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
        if resp.stop_reason != "tool_use":
            return text_of(resp)
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": b.id,
             "content": json.dumps(ORDERS.get(b.input["order_id"], {"error": "not_found"}))}
            for b in resp.content if getattr(b, "type", "") == "tool_use"]})
    return "Sorry, I couldn't finish that. A team member will follow up."

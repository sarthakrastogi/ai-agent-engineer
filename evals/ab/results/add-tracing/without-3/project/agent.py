"""Inbox agent: reads one inbound customer email and handles it with tools."""
import json

from llm import MODEL, complete, text_of
from tools import TOOLS, run_tool
from tracing import span

SYSTEM_PROMPT = """You are Parcelly's email support agent. You receive one customer email at a
time. Use the tools to look up orders and to reply to the customer. Be concise and polite."""

MAX_STEPS = 8


def handle_email(sender: str, subject: str, body: str) -> list[dict]:
    """Run the tool loop for one email. Returns the message transcript."""
    with span("handle_email") as root:
        root.content("sender", sender)
        root.content("subject", subject)
        root.content("body", body)
        messages = [{"role": "user", "content": f"From: {sender}\nSubject: {subject}\n\n{body}"}]
        outcome, tool_calls = "max_steps", []
        for step in range(MAX_STEPS):
            with span("llm.complete", step=step, model=MODEL) as s:
                resp = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
                s.set(stop_reason=resp.stop_reason, **_usage(resp))
                s.content("text", text_of(resp))
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                outcome = resp.stop_reason
                break
            results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    tool_calls.append(block.name)
                    with span("tool", tool=block.name, step=step) as s:
                        s.content("input", block.input)
                        out = run_tool(block.name, block.input)
                        s.set(tool_error=out.get("error") if isinstance(out, dict) else None)
                        s.content("output", out)
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out)})
            messages.append({"role": "user", "content": results})
        root.set(outcome=outcome, steps=step + 1, tool_calls=tool_calls,
                 replied="send_reply" in tool_calls)
        return messages


def _usage(resp) -> dict:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return {}
    return {"input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None)}

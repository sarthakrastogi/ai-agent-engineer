"""Inbox agent: reads one inbound customer email and handles it with tools."""
import json

from llm import MODEL, complete, text_of
from tools import TOOLS, run_tool
from tracing import include_content, span

SYSTEM_PROMPT = """You are Parcelly's email support agent. You receive one customer email at a
time. Use the tools to look up orders and to reply to the customer. Be concise and polite."""

MAX_STEPS = 8


def handle_email(sender: str, subject: str, body: str) -> list[dict]:
    """Run the tool loop for one email. Returns the message transcript."""
    messages = [{"role": "user", "content": f"From: {sender}\nSubject: {subject}\n\n{body}"}]
    with span("handle_email", model=MODEL, body_chars=len(body)) as email_attrs:
        if include_content():
            email_attrs.update(sender=sender, subject=subject, body=body)
        tool_calls = []
        email_attrs["outcome"] = "max_steps"  # overwritten if the model stops on its own
        for step in range(MAX_STEPS):
            with span("llm.complete", step=step, n_messages=len(messages)) as llm_attrs:
                resp = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
                llm_attrs["stop_reason"] = resp.stop_reason
                usage = getattr(resp, "usage", None)
                if usage is not None:
                    llm_attrs["input_tokens"] = getattr(usage, "input_tokens", None)
                    llm_attrs["output_tokens"] = getattr(usage, "output_tokens", None)
                if include_content():
                    llm_attrs["text"] = text_of(resp)
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                email_attrs["outcome"] = resp.stop_reason
                break
            results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    tool_calls.append(block.name)
                    with span("tool." + block.name, step=step, tool_use_id=block.id,
                              arg_keys=sorted(block.input)) as tool_attrs:
                        if include_content():
                            tool_attrs["input"] = block.input
                        out = run_tool(block.name, block.input)
                        tool_attrs["tool_error"] = out.get("error") if isinstance(out, dict) else None
                        if include_content():
                            tool_attrs["output"] = out
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out)})
            messages.append({"role": "user", "content": results})
        email_attrs["steps"] = step + 1
        email_attrs["tool_calls"] = tool_calls
        email_attrs["replied"] = "send_reply" in tool_calls
    return messages

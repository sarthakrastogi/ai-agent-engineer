"""Inbox agent: reads one inbound customer email and handles it with tools."""
import json

from llm import MODEL, complete, text_of
from tools import TOOLS, run_tool
from tracing import content, span

SYSTEM_PROMPT = """You are Parcelly's email support agent. You receive one customer email at a
time. Use the tools to look up orders and to reply to the customer. Be concise and polite."""

MAX_STEPS = 8


def handle_email(sender: str, subject: str, body: str) -> list[dict]:
    """Run the tool loop for one email. Returns the message transcript."""
    with span("handle_email", sender_domain=sender.rpartition("@")[2],
              subject=content(subject), body=content(body), body_chars=len(body)) as root:
        messages = [{"role": "user", "content": f"From: {sender}\nSubject: {subject}\n\n{body}"}]
        tools_called: list[str] = []
        stop_reason = None
        steps = 0
        for step in range(MAX_STEPS):
            steps = step + 1
            with span("llm.complete", step=step, model=MODEL) as s:
                resp = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
                stop_reason = resp.stop_reason
                usage = getattr(resp, "usage", None)
                s.set(stop_reason=stop_reason,
                      input_tokens=getattr(usage, "input_tokens", None),
                      output_tokens=getattr(usage, "output_tokens", None),
                      text=content(text_of(resp)))
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                break
            results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    with span("tool." + block.name, step=step, tool=block.name,
                              tool_use_id=block.id, input=content(block.input)) as s:
                        out = run_tool(block.name, block.input)
                        s.set(output=content(out), tool_error=out.get("error"))
                    tools_called.append(block.name)
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out)})
            messages.append({"role": "user", "content": results})
        root.set(steps=steps, final_stop_reason=stop_reason, tools_called=tools_called,
                 replied="send_reply" in tools_called,
                 hit_max_steps=stop_reason == "tool_use")
        return messages

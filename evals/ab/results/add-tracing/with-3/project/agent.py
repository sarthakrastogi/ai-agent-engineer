"""Inbox agent: reads one inbound customer email and handles it with tools."""
import hashlib
import json

from opentelemetry.trace import Status, StatusCode

from llm import MODEL, complete, text_of
from tools import TOOLS, run_tool
from tracing import CAPTURE_CONTENT, tracer

SYSTEM_PROMPT = """You are Parcelly's email support agent. You receive one customer email at a
time. Use the tools to look up orders and to reply to the customer. Be concise and polite."""
PROMPT_VERSION = hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:12]

MAX_STEPS = 8


def handle_email(sender: str, subject: str, body: str, *,
                 thread_id: str | None = None) -> list[dict]:
    """Run the tool loop for one email. Returns the message transcript.

    `thread_id` (e.g. the email thread's Message-ID) groups traces for one conversation.
    """
    with tracer.start_as_current_span("invoke_agent inbox_agent") as root:
        root.set_attributes({
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "inbox_agent",
            "gen_ai.provider.name": "anthropic",
            "gen_ai.request.model": MODEL,
            "app.prompt.version": PROMPT_VERSION,
        })
        if thread_id:
            root.set_attribute("gen_ai.conversation.id", thread_id)
        if CAPTURE_CONTENT:
            root.set_attribute("gen_ai.input.messages", json.dumps(
                [{"role": "user", "from": sender, "subject": subject, "body": body}]))

        messages = [{"role": "user", "content": f"From: {sender}\nSubject: {subject}\n\n{body}"}]
        replies_sent = 0
        steps = 0
        resp = None
        for _ in range(MAX_STEPS):
            steps += 1
            resp = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                break
            results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    out = _traced_tool(block, sender)
                    if block.name == "send_reply" and out.get("sent"):
                        replies_sent += 1
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out)})
            messages.append({"role": "user", "content": results})

        hit_max_steps = resp is not None and resp.stop_reason == "tool_use"
        root.set_attributes({
            "app.steps": steps,
            "app.stop_reason": resp.stop_reason if resp else "",
            "app.hit_max_steps": hit_max_steps,
            "app.replies_sent": replies_sent,
        })
        if CAPTURE_CONTENT and resp is not None:
            root.set_attribute("gen_ai.output.messages", text_of(resp))
        if hit_max_steps:
            root.set_status(Status(StatusCode.ERROR, "step limit reached"))
            root.set_attribute("error.type", "max_steps")
        return messages


def _traced_tool(block, sender: str) -> dict:
    with tracer.start_as_current_span(f"execute_tool {block.name}") as span:
        span.set_attributes({
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": block.name,
            "gen_ai.tool.call.id": block.id,
        })
        if CAPTURE_CONTENT:
            span.set_attribute("gen_ai.tool.call.arguments", json.dumps(block.input))
        if block.name == "send_reply":
            # Flags replies to anyone other than the sender without recording either address.
            to = str(block.input.get("to", "")).strip().lower()
            span.set_attribute("app.reply.to_is_sender", to == sender.strip().lower())
        out = run_tool(block.name, block.input)
        if "error" in out:
            # Returned to the model rather than raised, so mark it here or it is invisible.
            span.set_attribute("app.tool.result_anomalous", True)
            span.set_attribute("error.type", "tool_error")
            span.set_status(Status(StatusCode.ERROR, out["error"]))
        if CAPTURE_CONTENT:
            span.set_attribute("gen_ai.tool.call.result", json.dumps(out))
        return out

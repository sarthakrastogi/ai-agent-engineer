"""Inbox agent: reads one inbound customer email and handles it with tools."""
import hashlib
import json

from opentelemetry.trace import Status, StatusCode

from llm import MODEL, complete, text_of
from tools import TOOLS, run_tool
from tracing import RELEASE, set_content, tracer

SYSTEM_PROMPT = """You are Parcelly's email support agent. You receive one customer email at a
time. Use the tools to look up orders and to reply to the customer. Be concise and polite."""
PROMPT_VERSION = hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:12]

AGENT_NAME = "inbox_agent"
MAX_STEPS = 8


def handle_email(sender: str, subject: str, body: str,
                 conversation_id: str | None = None) -> list[dict]:
    """Run the tool loop for one email. Returns the message transcript.

    `conversation_id` (e.g. the email thread ID) groups traces for the same thread.
    """
    with tracer.start_as_current_span(f"invoke_agent {AGENT_NAME}") as span:
        span.set_attributes({
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": AGENT_NAME,
            "gen_ai.provider.name": "anthropic",
            "gen_ai.request.model": MODEL,
            "app.release": RELEASE,
            "app.prompt.version": PROMPT_VERSION,
        })
        if conversation_id:
            span.set_attribute("gen_ai.conversation.id", conversation_id)
        set_content(span, "app.email.sender", sender)
        set_content(span, "app.email.subject", subject)
        set_content(span, "app.email.body", body)

        messages = [{"role": "user", "content": f"From: {sender}\nSubject: {subject}\n\n{body}"}]
        replies_sent = 0
        finished = False
        steps = 0
        for steps in range(1, MAX_STEPS + 1):
            resp = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                finished = True
                set_content(span, "app.agent.final_text", text_of(resp))
                break
            results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    out = _traced_tool(block)
                    if block.name == "send_reply" and out.get("sent"):
                        replies_sent += 1
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out)})
            messages.append({"role": "user", "content": results})

        span.set_attributes({
            "app.agent.steps": steps,
            "app.agent.max_steps_reached": not finished,
            "app.agent.replies_sent": replies_sent,
        })
        if not finished:
            span.set_status(Status(StatusCode.ERROR, "max steps reached"))
        return messages


def _traced_tool(block) -> dict:
    with tracer.start_as_current_span(f"execute_tool {block.name}") as span:
        span.set_attributes({
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": block.name,
            "gen_ai.tool.call.id": block.id,
            "gen_ai.tool.type": "function",
        })
        set_content(span, "gen_ai.tool.call.arguments", block.input)
        out = run_tool(block.name, block.input)
        set_content(span, "gen_ai.tool.call.result", out)
        if not out or "error" in out:
            # Tool "succeeded" but returned nothing useful (unknown order, unknown tool).
            span.set_attribute("app.tool.result_anomalous", True)
            span.set_attribute("error.type", "tool_error" if out else "empty_result")
        return out

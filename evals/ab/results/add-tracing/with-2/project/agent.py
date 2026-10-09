"""Inbox agent: reads one inbound customer email and handles it with tools."""
import hashlib
import json

from opentelemetry.trace import Status, StatusCode

from llm import MODEL, complete, text_of
from telemetry import set_content, tracer
from tools import TOOLS, run_tool

SYSTEM_PROMPT = """You are Parcelly's email support agent. You receive one customer email at a
time. Use the tools to look up orders and to reply to the customer. Be concise and polite."""
PROMPT_VERSION = hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:12]

MAX_STEPS = 8
SIDE_EFFECT_TOOLS = {"send_reply"}


def _run_tool_traced(block) -> dict:
    with tracer.start_as_current_span(f"execute_tool {block.name}") as span:
        span.set_attribute("gen_ai.operation.name", "execute_tool")
        span.set_attribute("gen_ai.tool.name", block.name)
        span.set_attribute("gen_ai.tool.call.id", block.id)
        span.set_attribute("app.tool.side_effect", block.name in SIDE_EFFECT_TOOLS)
        set_content(span, "gen_ai.tool.call.arguments", block.input)
        out = run_tool(block.name, block.input)
        set_content(span, "gen_ai.tool.call.result", out)
        if not out or "error" in out:
            # Tools report failures as {"error": ...} rather than raising; surface them.
            span.set_attribute("app.tool.result_anomalous", True)
            span.set_status(Status(StatusCode.ERROR, str(out.get("error", "empty result"))))
        return out


def handle_email(sender: str, subject: str, body: str, email_id: str | None = None) -> list[dict]:
    """Run the tool loop for one email. Returns the message transcript."""
    with tracer.start_as_current_span("invoke_agent inbox_agent") as root:
        root.set_attribute("gen_ai.operation.name", "invoke_agent")
        root.set_attribute("gen_ai.agent.name", "inbox_agent")
        root.set_attribute("gen_ai.request.model", MODEL)
        root.set_attribute("app.prompt.version", PROMPT_VERSION)
        if email_id:
            root.set_attribute("gen_ai.conversation.id", email_id)
        set_content(root, "app.email.subject", subject)

        messages = [{"role": "user", "content": f"From: {sender}\nSubject: {subject}\n\n{body}"}]
        steps, tools_called, replied = 0, [], False
        for _ in range(MAX_STEPS):
            steps += 1
            resp = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                break
            results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    out = _run_tool_traced(block)
                    tools_called.append(block.name)
                    replied = replied or (block.name == "send_reply" and out.get("sent") is True)
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out)})
            messages.append({"role": "user", "content": results})

        root.set_attribute("app.agent.steps", steps)
        root.set_attribute("app.agent.tools_called", tools_called)
        root.set_attribute("app.agent.final_stop_reason", resp.stop_reason or "")
        root.set_attribute("app.agent.max_steps_reached", resp.stop_reason == "tool_use")
        # An email that ends without a reply is the main silent failure for this agent.
        root.set_attribute("app.agent.replied", replied)
        set_content(root, "app.agent.final_text", text_of(resp))
        return messages

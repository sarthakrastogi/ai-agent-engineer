from types import SimpleNamespace as NS

import pytest

pytest.importorskip("opentelemetry.sdk")
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import agent
import llm

EXPORTER = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(EXPORTER))
trace.set_tracer_provider(_provider)

USAGE = NS(input_tokens=100, output_tokens=20, cache_read_input_tokens=0,
           cache_creation_input_tokens=0)


def _tool(id_, name, input_):
    return NS(type="tool_use", id=id_, name=name, input=input_)


def _scripted(responses):
    it = iter(responses)
    return lambda **kwargs: next(it)


@pytest.fixture(autouse=True)
def _clear(monkeypatch):
    EXPORTER.clear()
    monkeypatch.delenv("TRACE_CONTENT", raising=False)


def _spans():
    return {s.name: s for s in EXPORTER.get_finished_spans()}, EXPORTER.get_finished_spans()


def test_span_tree_for_lookup_and_reply(monkeypatch):
    monkeypatch.setattr(llm, "_create", _scripted([
        NS(id="m1", model="m", stop_reason="tool_use", usage=USAGE,
           content=[_tool("t1", "lookup_order", {"order_id": "PCL-10482"})]),
        NS(id="m2", model="m", stop_reason="tool_use", usage=USAGE,
           content=[_tool("t2", "send_reply", {"to": "a@b.c", "body": "secret body"})]),
        NS(id="m3", model="m", stop_reason="end_turn", usage=USAGE,
           content=[NS(type="text", text="Done.")]),
    ]))
    agent.handle_email("a@b.c", "Where is my order", "PCL-10482 please", email_id="e-1")

    by_name, spans = _spans()
    root = by_name["invoke_agent inbox_agent"]
    assert root.parent is None
    assert root.attributes["gen_ai.conversation.id"] == "e-1"
    assert root.attributes["app.agent.replied"] is True
    assert root.attributes["app.agent.max_steps_reached"] is False
    assert root.attributes["app.agent.steps"] == 3

    chats = [s for s in spans if s.name.startswith("chat ")]
    tools = [s for s in spans if s.name.startswith("execute_tool ")]
    assert len(chats) == 3 and len(tools) == 2
    assert all(s.parent.span_id == root.context.span_id for s in chats + tools)
    assert all(s.context.trace_id == root.context.trace_id for s in spans)
    assert chats[0].attributes["gen_ai.usage.input_tokens"] == 100
    assert tools[1].attributes["app.tool.side_effect"] is True
    # Content capture is off by default: no email or reply text in any span.
    for s in spans:
        assert not any("secret body" in str(v) for v in s.attributes.values())


def test_tool_error_and_max_steps_are_flagged(monkeypatch):
    bad = NS(id="m", model="m", stop_reason="tool_use", usage=USAGE,
             content=[_tool("t", "lookup_order", {"order_id": "PCL-0"})])
    monkeypatch.setattr(llm, "_create", lambda **kw: bad)
    agent.handle_email("a@b.c", "s", "b")

    by_name, spans = _spans()
    root = by_name["invoke_agent inbox_agent"]
    assert root.attributes["app.agent.max_steps_reached"] is True
    assert root.attributes["app.agent.replied"] is False
    tool = next(s for s in spans if s.name == "execute_tool lookup_order")
    assert tool.attributes["app.tool.result_anomalous"] is True
    assert tool.status.status_code == trace.StatusCode.ERROR


def test_model_exception_marks_spans_error(monkeypatch):
    def boom(**kw):
        raise RuntimeError("overloaded")
    monkeypatch.setattr(llm, "_create", boom)
    with pytest.raises(RuntimeError):
        agent.handle_email("a@b.c", "s", "b")
    by_name, _ = _spans()
    assert by_name["invoke_agent inbox_agent"].status.status_code == trace.StatusCode.ERROR
    assert by_name[f"chat {llm.MODEL}"].events[0].name == "exception"


def test_content_captured_when_enabled(monkeypatch):
    monkeypatch.setenv("TRACE_CONTENT", "1")
    monkeypatch.setattr(llm, "_create", _scripted([
        NS(id="m", model="m", stop_reason="end_turn", usage=USAGE,
           content=[NS(type="text", text="Hi")]),
    ]))
    agent.handle_email("a@b.c", "s", "my body")
    by_name, _ = _spans()
    assert "my body" in by_name[f"chat {llm.MODEL}"].attributes["gen_ai.input.messages"]

from types import SimpleNamespace as NS

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import agent
import llm
import tracing

EXPORTER = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(EXPORTER))
trace.set_tracer_provider(_provider)


def _resp(stop_reason, *content):
    return NS(id="msg_1", model=llm.MODEL, stop_reason=stop_reason, content=list(content),
              usage=NS(input_tokens=100, output_tokens=20,
                       cache_read_input_tokens=0, cache_creation_input_tokens=0))


def _tool_use(id_, name, input_):
    return NS(type="tool_use", id=id_, name=name, input=input_)


@pytest.fixture(autouse=True)
def _clear():
    EXPORTER.clear()
    yield


def _run(monkeypatch, responses):
    it = iter(responses)
    monkeypatch.setattr(llm, "_create", lambda **kw: next(it))
    agent.handle_email("ana@example.com", "Lamp", "Where is PCL-10482?", conversation_id="t-1")
    return {s.name: s for s in EXPORTER.get_finished_spans()}, EXPORTER.get_finished_spans()


def test_span_tree(monkeypatch):
    by_name, spans = _run(monkeypatch, [
        _resp("tool_use", _tool_use("t1", "lookup_order", {"order_id": "PCL-10482"})),
        _resp("tool_use", _tool_use("t2", "send_reply", {"to": "ana@example.com", "body": "Hi"})),
        _resp("end_turn", NS(type="text", text="Done")),
    ])
    root = by_name["invoke_agent inbox_agent"]
    assert root.parent is None
    assert len({s.context.trace_id for s in spans}) == 1
    chats = [s for s in spans if s.name == f"chat {llm.MODEL}"]
    assert len(chats) == 3
    assert all(s.parent.span_id == root.context.span_id for s in spans if s is not root)
    assert by_name["execute_tool lookup_order"].attributes["gen_ai.tool.call.id"] == "t1"
    assert chats[0].attributes["gen_ai.usage.input_tokens"] == 100
    assert root.attributes["gen_ai.conversation.id"] == "t-1"
    assert root.attributes["app.agent.replies_sent"] == 1
    assert root.attributes["app.agent.max_steps_reached"] is False


def test_no_content_recorded_by_default(monkeypatch):
    assert not tracing.CAPTURE_CONTENT
    _, spans = _run(monkeypatch, [_resp("end_turn", NS(type="text", text="Done"))])
    for s in spans:
        for value in s.attributes.values():
            assert "ana@example.com" not in str(value) and "PCL-10482" not in str(value)


def test_bad_tool_result_and_runaway_loop_are_flagged(monkeypatch):
    loop = [_resp("tool_use", _tool_use(f"t{i}", "lookup_order", {"order_id": "PCL-0"}))
            for i in range(agent.MAX_STEPS)]
    by_name, _ = _run(monkeypatch, loop)
    assert by_name["execute_tool lookup_order"].attributes["app.tool.result_anomalous"] is True
    root = by_name["invoke_agent inbox_agent"]
    assert root.attributes["app.agent.max_steps_reached"] is True
    assert root.status.status_code == trace.StatusCode.ERROR


def test_llm_error_is_recorded(monkeypatch):
    def boom(**kw):
        raise RuntimeError("overloaded")
    monkeypatch.setattr(llm, "_create", boom)
    with pytest.raises(RuntimeError):
        agent.handle_email("a@b.c", "s", "b")
    chat = next(s for s in EXPORTER.get_finished_spans() if s.name.startswith("chat"))
    assert chat.status.status_code == trace.StatusCode.ERROR

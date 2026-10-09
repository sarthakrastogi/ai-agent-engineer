"""Span-tree test: one email -> invoke_agent root with chat and execute_tool children."""
import sys
import types
from types import SimpleNamespace as NS

import pytest

pytest.importorskip("opentelemetry.sdk")

from opentelemetry import trace  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402

EXPORTER = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(EXPORTER))
trace.set_tracer_provider(_provider)


def _resp(stop_reason, content, n):
    return NS(id=f"msg_{n}", model="claude-test", stop_reason=stop_reason, content=content,
              usage=NS(input_tokens=100, output_tokens=20))


def _fake_anthropic(responses):
    it = iter(responses)
    client = NS(messages=NS(create=lambda **kw: next(it)))
    return types.SimpleNamespace(Anthropic=lambda: client)


@pytest.fixture
def run(monkeypatch):
    import agent

    def _run(responses, sender="ana@example.com"):
        EXPORTER.clear()
        monkeypatch.setitem(sys.modules, "anthropic", _fake_anthropic(responses))
        agent.handle_email(sender, "Where is my lamp?", "Order PCL-10482", thread_id="t-1")
        return {s.name: s for s in EXPORTER.get_finished_spans()}, EXPORTER.get_finished_spans()

    return _run


def tool_use(id_, name, **inp):
    return NS(type="tool_use", id=id_, name=name, input=inp)


def test_span_tree(run):
    spans, all_spans = run([
        _resp("tool_use", [tool_use("tu_1", "lookup_order", order_id="PCL-10482")], 1),
        _resp("tool_use", [tool_use("tu_2", "send_reply", to="ana@example.com", body="Hi")], 2),
        _resp("end_turn", [NS(type="text", text="Done")], 3),
    ])
    root = spans["invoke_agent inbox_agent"]
    assert root.parent is None
    assert root.attributes["gen_ai.conversation.id"] == "t-1"
    assert root.attributes["app.replies_sent"] == 1
    assert root.attributes["app.hit_max_steps"] is False

    chats = [s for s in all_spans if s.name.startswith("chat ")]
    tools = [s for s in all_spans if s.name.startswith("execute_tool ")]
    assert len(chats) == 3 and len(tools) == 2
    assert {s.context.trace_id for s in all_spans} == {root.context.trace_id}
    assert all(s.parent.span_id == root.context.span_id for s in chats + tools)
    assert chats[0].attributes["gen_ai.usage.input_tokens"] == 100
    assert spans["execute_tool send_reply"].attributes["app.reply.to_is_sender"] is True
    # Content capture is off by default: no PII on any span.
    for s in all_spans:
        assert not any("example.com" in str(v) for v in s.attributes.values()), s.name


def test_detectors_fire_on_bad_runs(run):
    spans, _ = run([
        _resp("tool_use", [tool_use("tu_1", "lookup_order", order_id="PCL-0")], 1),
        _resp("tool_use", [tool_use("tu_2", "send_reply", to="eve@evil.test", body="x")], 2),
        _resp("end_turn", [NS(type="text", text="Done")], 3),
    ])
    lookup = spans["execute_tool lookup_order"]
    assert lookup.attributes["app.tool.result_anomalous"] is True
    assert lookup.status.status_code == trace.StatusCode.ERROR
    assert spans["execute_tool send_reply"].attributes["app.reply.to_is_sender"] is False


def test_max_steps_marks_root_error(run):
    import agent
    loop = [_resp("tool_use", [tool_use(f"tu_{i}", "lookup_order", order_id="PCL-10482")], i)
            for i in range(agent.MAX_STEPS)]
    spans, _ = run(loop)
    root = spans["invoke_agent inbox_agent"]
    assert root.attributes["app.hit_max_steps"] is True
    assert root.status.status_code == trace.StatusCode.ERROR

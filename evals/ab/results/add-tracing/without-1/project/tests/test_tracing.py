from types import SimpleNamespace as NS

import pytest

import agent
import tracing


def _resp(stop_reason, *blocks):
    return NS(stop_reason=stop_reason, content=list(blocks),
              usage=NS(input_tokens=100, output_tokens=20))


@pytest.fixture
def spans(monkeypatch):
    recorded = []
    monkeypatch.setattr(tracing, "EXPORTERS", [recorded.append])
    return recorded


def test_handle_email_emits_nested_spans(monkeypatch, spans):
    replies = iter([
        _resp("tool_use", NS(type="tool_use", id="t1", name="lookup_order",
                             input={"order_id": "PCL-10482"})),
        _resp("end_turn", NS(type="text", text="Done")),
    ])
    monkeypatch.setattr(agent, "complete", lambda **kw: next(replies))

    agent.handle_email("jo@example.com", "Where is my order?", "PCL-10482 please")

    names = [s["name"] for s in spans]
    assert names == ["llm.complete", "tool.lookup_order", "llm.complete", "handle_email"]
    root = spans[-1]
    assert {s["trace_id"] for s in spans} == {root["trace_id"]}
    assert all(s["parent_id"] == root["span_id"] for s in spans[:-1])
    assert root["attrs"]["sender_domain"] == "example.com"
    assert root["attrs"]["tools_called"] == ["lookup_order"]
    assert root["attrs"]["final_stop_reason"] == "end_turn"
    assert spans[0]["attrs"]["input_tokens"] == 100
    # customer content is redacted by default
    assert root["attrs"]["body"] == "[redacted]"
    assert spans[1]["attrs"]["input"] == "[redacted]"


def test_errors_are_recorded_and_reraised(monkeypatch, spans):
    def boom(**kw):
        raise RuntimeError("api down")
    monkeypatch.setattr(agent, "complete", boom)

    with pytest.raises(RuntimeError):
        agent.handle_email("jo@example.com", "hi", "hi")

    assert [s["status"] for s in spans] == ["error", "error"]
    assert spans[0]["attrs"]["error"] == "RuntimeError: api down"

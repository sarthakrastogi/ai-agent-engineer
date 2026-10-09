import json
from types import SimpleNamespace as NS

import agent
import tools


def _fake_llm(responses):
    it = iter(responses)
    return lambda **kw: next(it)


def _spans(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_handle_email_emits_nested_spans(tmp_path, monkeypatch):
    trace = tmp_path / "trace.jsonl"
    monkeypatch.setenv("INBOX_TRACE_FILE", str(trace))
    monkeypatch.delenv("INBOX_TRACE_CONTENT", raising=False)
    monkeypatch.setattr(agent, "complete", _fake_llm([
        NS(stop_reason="tool_use", usage=NS(input_tokens=50, output_tokens=10), content=[
            NS(type="tool_use", id="t1", name="lookup_order", input={"order_id": "PCL-0"})]),
        NS(stop_reason="end_turn", usage=NS(input_tokens=80, output_tokens=5),
           content=[NS(type="text", text="Done")]),
    ]))

    agent.handle_email("a@b.com", "Where is my order", "secret body")

    spans = _spans(trace)
    assert [s["name"] for s in spans] == ["llm.complete", "tool.lookup_order",
                                         "llm.complete", "handle_email"]
    root = spans[-1]
    assert root["parent_id"] is None and root["status"] == "ok"
    assert all(s["trace_id"] == root["trace_id"] for s in spans)
    assert all(s["parent_id"] == root["span_id"] for s in spans[:-1])
    assert root["attrs"]["outcome"] == "end_turn"
    assert root["attrs"]["tool_calls"] == ["lookup_order"]
    assert root["attrs"]["replied"] is False
    assert spans[0]["attrs"]["input_tokens"] == 50
    assert spans[1]["attrs"]["tool_error"] == "No order PCL-0"
    assert "secret body" not in trace.read_text() and "a@b.com" not in trace.read_text()


def test_tool_exception_is_recorded(tmp_path, monkeypatch):
    trace = tmp_path / "trace.jsonl"
    monkeypatch.setenv("INBOX_TRACE_FILE", str(trace))
    monkeypatch.setattr(agent, "complete", _fake_llm([
        NS(stop_reason="tool_use", content=[
            NS(type="tool_use", id="t1", name="send_reply", input={"to": "x"})]),
    ]))

    try:
        agent.handle_email("a@b.com", "s", "b")
    except TypeError:
        pass

    spans = _spans(trace)
    assert [s["name"] for s in spans] == ["llm.complete", "tool.send_reply", "handle_email"]
    assert spans[1]["status"] == "error" and "TypeError" in spans[1]["error"]
    assert spans[2]["status"] == "error"
    assert tools.OUTBOX == []

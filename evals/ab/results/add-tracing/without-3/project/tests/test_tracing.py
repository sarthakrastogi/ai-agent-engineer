import json
import logging
from types import SimpleNamespace as NS

import agent
import tracing


def _fake_complete(responses):
    it = iter(responses)
    return lambda **kw: next(it)


def _spans(caplog):
    return [json.loads(r.message) for r in caplog.records if r.name == "inbox.trace"]


def test_handle_email_emits_linked_spans(monkeypatch, caplog):
    tool_use = NS(type="tool_use", id="t1", name="lookup_order", input={"order_id": "PCL-10482"})
    monkeypatch.setattr(agent, "complete", _fake_complete([
        NS(content=[tool_use], stop_reason="tool_use", usage=NS(input_tokens=10, output_tokens=5)),
        NS(content=[NS(type="text", text="done")], stop_reason="end_turn", usage=None),
    ]))
    monkeypatch.setattr(tracing, "RECORD_CONTENT", False)
    caplog.set_level(logging.INFO, logger="inbox.trace")

    agent.handle_email("a@example.com", "Where is my order", "PCL-10482 please")

    spans = _spans(caplog)
    assert [s["name"] for s in spans] == ["llm.complete", "tool", "llm.complete", "handle_email"]
    root = spans[-1]
    assert {s["trace_id"] for s in spans} == {root["trace_id"]}
    assert all(s["parent_id"] == root["span_id"] for s in spans[:-1])
    assert root["outcome"] == "end_turn" and root["steps"] == 2 and root["replied"] is False
    assert spans[0]["input_tokens"] == 10 and spans[1]["tool"] == "lookup_order"
    # PII is not recorded by default, only its size.
    assert "body" not in root and root["body_chars"] == len("PCL-10482 please")


def test_tool_exception_is_recorded_and_reraised(monkeypatch, caplog):
    bad = NS(type="tool_use", id="t1", name="lookup_order", input={"wrong": 1})
    monkeypatch.setattr(agent, "complete", _fake_complete([
        NS(content=[bad], stop_reason="tool_use"),
    ]))
    caplog.set_level(logging.INFO, logger="inbox.trace")

    try:
        agent.handle_email("a@example.com", "s", "b")
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError")

    spans = _spans(caplog)
    assert [s["status"] for s in spans if s["name"] in ("tool", "handle_email")] == ["error", "error"]
    assert "TypeError" in spans[-1]["error"]

"""Minimal span tracing for the inbox agent.

Each finished span is passed to every function in EXPORTERS. The default exporter writes one JSON
line per span to stderr. Customer content (email bodies, reply text, tool payloads) is only
recorded when TRACE_CONTENT=1; use `content()` for anything that may contain PII.
"""
import contextvars
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager

CAPTURE_CONTENT = os.environ.get("TRACE_CONTENT") == "1"

_current: contextvars.ContextVar["Span | None"] = contextvars.ContextVar("span", default=None)


class Span:
    def __init__(self, name: str, parent: "Span | None"):
        self.name = name
        self.trace_id = parent.trace_id if parent else uuid.uuid4().hex
        self.span_id = uuid.uuid4().hex[:16]
        self.parent_id = parent.span_id if parent else None
        self.attrs: dict = {}

    def set(self, **attrs) -> None:
        self.attrs.update(attrs)


def content(value):
    """Return value if content capture is on, else a redaction marker."""
    return value if CAPTURE_CONTENT else "[redacted]"


def _stderr_exporter(record: dict) -> None:
    print(json.dumps(record, default=str), file=sys.stderr, flush=True)


EXPORTERS = [_stderr_exporter]


@contextmanager
def span(name: str, **attrs):
    s = Span(name, _current.get())
    s.set(**attrs)
    token = _current.set(s)
    start = time.time()
    status = "ok"
    try:
        yield s
    except BaseException as e:
        status = "error"
        s.set(error=f"{type(e).__name__}: {e}")
        raise
    finally:
        _current.reset(token)
        record = {"name": s.name, "trace_id": s.trace_id, "span_id": s.span_id,
                  "parent_id": s.parent_id, "start": start,
                  "duration_ms": round((time.time() - start) * 1000, 1),
                  "status": status, "attrs": s.attrs}
        for export in EXPORTERS:
            try:
                export(record)
            except Exception:
                pass  # tracing must never break email handling

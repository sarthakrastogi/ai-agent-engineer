"""Minimal span tracing: one JSON line per finished span on the `inbox.trace` logger.

Spans nest via contextvars, so every LLM call and tool call is tied to the email that caused it
by `trace_id`. Message contents (email bodies, reply text, addresses) are NOT recorded unless
TRACE_CONTENT=1, because they are customer PII; by default only sizes and metadata are logged.
"""
import contextlib
import contextvars
import json
import logging
import os
import time
import uuid

logger = logging.getLogger("inbox.trace")

RECORD_CONTENT = os.environ.get("TRACE_CONTENT") == "1"
MAX_CONTENT_CHARS = 2000

_current: contextvars.ContextVar["Span | None"] = contextvars.ContextVar("span", default=None)


class Span:
    def __init__(self, name: str, attrs: dict):
        parent = _current.get()
        self.name = name
        self.trace_id = parent.trace_id if parent else uuid.uuid4().hex
        self.span_id = uuid.uuid4().hex[:16]
        self.parent_id = parent.span_id if parent else None
        self.attrs = dict(attrs)
        self.start = time.time()

    def set(self, **attrs) -> None:
        self.attrs.update(attrs)

    def content(self, key: str, value) -> None:
        """Record a payload only when content capture is enabled; always record its size."""
        text = value if isinstance(value, str) else json.dumps(value, default=str)
        self.attrs[f"{key}_chars"] = len(text)
        if RECORD_CONTENT:
            self.attrs[key] = text[:MAX_CONTENT_CHARS]


@contextlib.contextmanager
def span(name: str, **attrs):
    s = Span(name, attrs)
    token = _current.set(s)
    status, error = "ok", None
    try:
        yield s
    except BaseException as e:
        status, error = "error", f"{type(e).__name__}: {e}"
        raise
    finally:
        _current.reset(token)
        record = {"trace_id": s.trace_id, "span_id": s.span_id, "parent_id": s.parent_id,
                  "name": s.name, "start": s.start,
                  "duration_ms": round((time.time() - s.start) * 1000, 1),
                  "status": status, **s.attrs}
        if error:
            record["error"] = error
        logger.info(json.dumps(record, default=str))

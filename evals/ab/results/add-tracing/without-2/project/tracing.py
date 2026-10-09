"""Minimal span tracing for the inbox agent: one JSON line per finished span.

Spans nest via contextvars, so every LLM and tool call inside `handle_email` shares the
email's trace_id. Output goes to the file named by INBOX_TRACE_FILE, else stderr.
Message bodies are left out unless INBOX_TRACE_CONTENT=1, since they hold customer PII.
"""
import contextvars
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager

_current: contextvars.ContextVar[dict | None] = contextvars.ContextVar("span", default=None)


def include_content() -> bool:
    return os.environ.get("INBOX_TRACE_CONTENT") == "1"


def _emit(record: dict) -> None:
    line = json.dumps(record, default=str)
    path = os.environ.get("INBOX_TRACE_FILE")
    if path:
        with open(path, "a") as f:
            f.write(line + "\n")
    else:
        print(line, file=sys.stderr, flush=True)


@contextmanager
def span(name: str, **attrs):
    """Time a block and emit it as a span. Yields the attrs dict so callers can add to it."""
    parent = _current.get()
    rec = {"trace_id": parent["trace_id"] if parent else uuid.uuid4().hex,
           "span_id": uuid.uuid4().hex[:16],
           "parent_id": parent["span_id"] if parent else None,
           "name": name, "attrs": attrs}
    token = _current.set(rec)
    start = time.time()
    try:
        yield attrs
        rec["status"] = "ok"
    except BaseException as e:
        rec["status"] = "error"
        rec["error"] = f"{type(e).__name__}: {e}"
        raise
    finally:
        _current.reset(token)
        rec["start"] = start
        rec["duration_ms"] = round((time.time() - start) * 1000, 1)
        _emit(rec)

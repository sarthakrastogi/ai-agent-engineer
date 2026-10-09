# Parcelly inbox agent

`agent.handle_email(sender, subject, body)` runs the tool loop for one inbound customer email.
Tools are in `tools.py`; the payments client is `payments.py`. Tests: `python -m pytest`.

## Tracing

Each email produces one JSON line per span (`handle_email` → `llm.complete` / `tool.<name>`),
all sharing a `trace_id`. Spans record duration, status/error, stop reason, token usage,
tool calls and tool errors, and the final `outcome` (`end_turn`, `max_tokens`, `max_steps`, …).

- `INBOX_TRACE_FILE=/path/trace.jsonl` writes there instead of stderr.
- `INBOX_TRACE_CONTENT=1` also records email text, model text and tool inputs/outputs.
  These contain customer PII, so leave it off in production unless you need it.

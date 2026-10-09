# Parcelly inbox agent

`agent.handle_email(sender, subject, body)` runs the tool loop for one inbound customer email.
Tools are in `tools.py`; the payments client is `payments.py`. Tests: `python -m pytest`.

## Tracing

Each email produces one JSON line per span on the `inbox.trace` logger (INFO level): a
`handle_email` root span (outcome, steps, tools called, whether a reply was sent) with child
`llm.complete` spans (model, stop_reason, tokens, latency) and `tool` spans (tool name, latency,
errors), all sharing a `trace_id`. Configure logging to ship that logger at INFO, e.g.
`logging.basicConfig(level=logging.INFO)`. Email/reply contents are omitted (sizes only) unless
`TRACE_CONTENT=1`.

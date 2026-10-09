# Parcelly inbox agent

`agent.handle_email(sender, subject, body)` runs the tool loop for one inbound customer email.
Tools are in `tools.py`; the payments client is `payments.py`. Tests: `python -m pytest`.

## Tracing

Every email produces one trace: a `handle_email` root span plus a `llm.complete` and `tool.<name>`
span for each step. By default each span is written as one JSON line to stderr. To send spans
somewhere else, add a function to `tracing.EXPORTERS`. Customer content (email body, subject,
model text, tool inputs and outputs) is redacted unless `TRACE_CONTENT=1`.

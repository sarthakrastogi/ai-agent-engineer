# Parcelly inbox agent

`agent.handle_email(sender, subject, body)` runs the tool loop for one inbound customer email.
Tools are in `tools.py`; the payments client is `payments.py`. Tests: `python -m pytest`.
Tracing: call `tracing.init_tracing()` at startup and set `OTEL_EXPORTER_OTLP_ENDPOINT`; see `observability.md`.

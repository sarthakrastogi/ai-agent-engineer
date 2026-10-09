# Parcelly inbox agent

`agent.handle_email(sender, subject, body)` runs the tool loop for one inbound customer email.
Tools are in `tools.py`; the payments client is `payments.py`. Tests: `python -m pytest`.

## Tracing

OpenTelemetry, GenAI semantic conventions (`OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`).
Each email produces one trace:

```
invoke_agent inbox_agent      release, prompt version, steps, replies_sent, max_steps_reached
├── chat claude-sonnet-5-5    model, finish reason, input/output/cache tokens
├── execute_tool lookup_order call id; app.tool.result_anomalous on error results
└── ...
```

Call `tracing.setup_tracing()` once at process start and `tracing.shutdown_tracing()` before
exit. Configure export with the standard env vars, e.g.
`OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318`. Set `APP_RELEASE` to the deployed version.

Email bodies, addresses, tool arguments and results are **not** recorded unless
`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`. Use that in dev only.

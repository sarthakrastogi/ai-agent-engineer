# Parcelly inbox agent

`agent.handle_email(sender, subject, body)` runs the tool loop for one inbound customer email.
Tools are in `tools.py`; the payments client is `payments.py`. Tests: `python -m pytest`.

## Tracing

OpenTelemetry, GenAI semantic conventions (experimental, `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`).
Requires `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`.
Call `telemetry.setup_tracing()` once at process start (skip it if the host app already configures OTel).

One trace per email:

```
invoke_agent inbox_agent        gen_ai.conversation.id (email_id), app.prompt.version,
│                               app.agent.steps / tools_called / replied / max_steps_reached
├── chat <model>                tokens (incl. cache), finish_reasons, response id/model
├── execute_tool lookup_order   gen_ai.tool.call.id, app.tool.result_anomalous (+ ERROR status)
└── execute_tool send_reply     app.tool.side_effect=true
```

Env: `OTEL_EXPORTER_OTLP_ENDPOINT` (Collector), `RELEASE`, `DEPLOY_ENV`.
Content (email text, tool args/results, model output) is recorded **only** with `TRACE_CONTENT=1`
because emails contain customer PII. Keep it off in production unless redaction is in place.

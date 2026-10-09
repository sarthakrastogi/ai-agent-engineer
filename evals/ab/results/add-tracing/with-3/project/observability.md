# Inbox agent observability

Schema: OpenTelemetry GenAI semantic conventions (experimental, written against the
2026 attribute names; expect renames). Manual spans, no instrumentor. Export: OTLP/HTTP
via the standard `OTEL_EXPORTER_OTLP_*` env vars, ideally to a Collector.

Call `tracing.init_tracing()` once at process start.

## Span tree (one trace per email)

```
invoke_agent inbox_agent        root; gen_ai.conversation.id = thread_id
├── chat <model>                one per model call: tokens, finish reason, response id
├── execute_tool lookup_order
├── execute_tool send_reply
└── chat <model> ...
```

## Attributes that matter for debugging

| Attribute | Span | Meaning |
|---|---|---|
| `app.prompt.version` | root | sha256[:12] of the system prompt |
| `service.version` / `deployment.environment.name` | resource | `APP_RELEASE` / `APP_ENV` |
| `app.steps`, `app.stop_reason` | root | loop length, final stop reason |
| `app.hit_max_steps` | root | loop exhausted (root status = ERROR) |
| `app.replies_sent` | root | 0 means the customer got no reply |
| `app.tool.result_anomalous` | tool | tool returned `{"error": ...}` (status = ERROR) |
| `app.reply.to_is_sender` | send_reply | `false` = reply went to someone other than the sender |

## Content and PII

Off by default: no email bodies, addresses, model text or tool args on spans.
`INBOX_TRACE_CONTENT=1` records them (`gen_ai.input/output.messages`,
`gen_ai.tool.call.arguments/result`). Use it in dev only unless a redacting Collector
or an external content store sits in front of the backend.

## Sampling

Keep 100% while volume is low. If you need to sample later, use Collector tail sampling
that keeps every ERROR trace and every `app.reply.to_is_sender=false`.

## Suggested alerts

- Any `app.reply.to_is_sender=false` (possible prompt-injected exfiltration).
- Rate of `app.replies_sent=0` or `app.hit_max_steps=true` above baseline.
- Tool-error rate per tool.

## Verification

`tests/test_tracing.py` checks the span tree, checks that PII is absent by default, and
feeds known-bad runs (unknown order, foreign recipient, step limit) to each detector.

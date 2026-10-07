# Content capture, PII and sampling

## Decide with the user first

Ask, and record under "PII handling" in `observability.md`:

- Which data classes appear in prompts and tool results (PII, health, financial,
  secrets, customer docs)? Residency or retention rules?
- Who may read raw content, for how long? Is error analysis on real conversations allowed?

## Capture modes

| Mode | Use for | How |
|---|---|---|
| No content (OTel default) | Strictest environments | Metadata only: tokens, latency, errors, IDs, versions, tool sequence |
| Content on span attributes | Dev, staging, internal tools | Instrumentation content flag on |
| **External store + reference on span** | **Production default** | Upload messages to a store with its own ACL and retention; record the URI on the span |

- External storage: everyone sees trace shape, only approved reviewers open content;
  uploads happen whether or not the span is sampled.
- Switches (verify against current provider docs):
  - OTel Python GenAI: `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=span_only|event_only|span_and_event`
    (older versions: `true/false`); `OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK=upload` +
    `OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH`.
  - OpenInference: `OPENINFERENCE_HIDE_INPUTS`, `_OUTPUTS`, `_INPUT_MESSAGES`, `_LLM_TOOLS`,
    `_RETRIEVAL_DOCUMENTS` → `"__REDACTED__"`.

## What to capture

- **Curated root input/output:** the user message and final answer, not raw function
  arguments. Evaluators and trace tables read the root.
- LLM call: model requested/served, tokens (cached, reasoning), finish reason, latency,
  cost, prompt name + version, messages per capture mode.
- Tool call: name, call ID, arguments, result (or truncated + size), error type.
- Retrieval: query and rewrites, data source, top-k, doc IDs, scores, content or refs —
  enough to score retrieval offline.
- Guardrail decisions, approvals, refusals.
- Audit test per span: does it show exactly what context the agent had when it decided?

## What not to capture

- Secrets: API keys, auth headers, tokens, connection strings.
- Whole configs, client objects, env dumps.
- Static system prompts and tool definitions on every call — record name + version, store
  content once.
- Large binaries inline — store and reference.
- PII not needed for debugging; hash or pseudonymise user IDs if required.
- Set `OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT` so a huge tool result can't drop the span batch.

## Where redaction runs

| Layer | Use for |
|---|---|
| In process, before export | Data that must never leave the service (SDK masking hook; deterministic, fast) |
| Collector `redaction` processor | Central policy across services; one place to audit |
| Backend masking | Last resort — data already left your control |

```yaml
processors:
  redaction:
    allow_all_keys: false
    allowed_keys: [gen_ai.operation.name, gen_ai.request.model, gen_ai.usage.input_tokens]
    blocked_values: ["4[0-9]{12}(?:[0-9]{3})?", "[\\w.-]+@[\\w.-]+\\.\\w+"]
    summary: info
```

With `allow_all_keys: false`, every needed attribute must be in `allowed_keys` or
dashboards go blank. Test on a trace with seeded fake PII before production.

## Sampling

- **Head sampling** decides before the outcome; it can't keep all errors.
- **Tail sampling** (Collector) decides after the trace completes. Stateful and
  memory-heavy; route all spans of a trace to the same Collector instance by trace ID.
- Random sampling under-represents LLM failures. Keep on outcome: errors, slow traces,
  failed in-path checks (grounding, validation), guardrail flags; sample routine
  successes at 5–20%.
- Sample whole traces, never individual spans.
- Sample online evals separately (e.g. judge 10% of kept traces plus all negative feedback).

| Environment | Keep |
|---|---|
| Dev, staging, eval runs | 100% |
| Production | 100% of errors, slow, flagged, failed-validation, and the newest release's first days; a ratio of the rest |
| Low volume (most internal agents) | 100% — rare edge cases are what sampling drops first |

```yaml
processors:
  tail_sampling:
    decision_wait: 30s
    policies:                      # kept if any policy matches
      - { name: errors,  type: status_code,   status_code:   { status_codes: [ERROR] } }
      - { name: slow,    type: latency,       latency:       { threshold_ms: 20000 } }
      - { name: release, type: string_attribute, string_attribute: { key: service.version, values: ["<new-sha>"] } }
      - { name: flagged, type: boolean_attribute, boolean_attribute: { key: app.guardrail.flagged, value: true } }
      - { name: failed_check, type: boolean_attribute, boolean_attribute: { key: app.validation.passed, value: false } }
      - { name: rest,    type: probabilistic, probabilistic: { sampling_percentage: 10 } }
```

**Feedback arrives after the sampling decision.** To keep negative-feedback traces, keep
100%, or rebuild them from external content storage keyed by trace ID.

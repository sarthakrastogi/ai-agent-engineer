# <Agent name> — observability

## Tracing
- SDK / instrumentation: <!-- fill: OTel GenAI semconv / OpenInference / vendor SDK -->
- Semconv version + opt-in: <!-- e.g. OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental -->
- Exporter → backend:
- Span hierarchy: agent run → LLM call / tool call / retrieval
- Attributes captured per span:
- PII handling (redaction, retention):
- Sampling:

## Key metrics
| Metric | Source | Target | Alert when |
|---|---|---|---|
| Task success rate (online eval) |  |  |  |
| p95 latency |  |  |  |
| Cost per task |  |  |  |
| Tool error rate |  |  |  |
| User feedback (thumbs down rate) |  |  |  |
| Tokens per turn / prompt-cache hit rate |  |  |  |
| Compactions per session (long-running agents) |  |  |  |

## Feedback loop
<!-- fill: how flagged traces get into datasets/ and the next error-analysis round -->

## Verification
- [ ] A test run produces one trace with the expected span tree
- [ ] Prompts, completions, tool args/results visible (or redacted on purpose)
- [ ] Token counts and cost present on LLM spans
- [ ] Errors show up as span errors, not just log lines

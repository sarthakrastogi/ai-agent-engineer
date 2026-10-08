# Metrics, dashboards, alerts and feedback

## Readiness test

Before production traffic, on-call must be able to answer for any run in the retention
window: what it did, why, what it cost — and for every side effect, which action ran, on
whose authority, from what input. If not, the gap is instrumentation, not dashboards.

## Core metrics

| Metric | Derived from | Watch for |
|---|---|---|
| Latency p50/p95/p99, TTFT | Root span duration; `gen_ai.client.operation.time_to_first_chunk` | Tail growth after a release |
| Tokens per run (input, cached, output, reasoning) | `gen_ai.usage.*` or usage counters | Context growth over a conversation |
| Cost per run / task / user | Tokens × price table, by model | Budget from `design.md` |
| LLM and tool calls per run | `gen_ai.invoke_agent.{inference_calls,tool_calls}` or child counts | Loops, runaway retries |
| Tool error rate by tool and `error.type` | `execute_tool` spans with ERROR | One tool degrading |
| `length` finish-reason rate | `gen_ai.response.finish_reasons` | Truncation, `max_tokens` too low |
| Retrieval signals | Top reranker score, empty-result rate | Weak query clusters (`agent-rag`) |
| Online eval pass rate per failure mode | Judge scores on sampled traces | Relative drops |
| Feedback and outcome rates | Feedback joined by trace ID | Thumbs-down spikes, edit rate |
| Guardrail trigger / refusal rate | Guardrail spans | Over-blocking after a change |
| Abstain / fallback rate | "Not enough info" or handoff ÷ all answers | **Near 0 is suspicious**: guessing on ambiguous input |
| Anomalous tool-result rate | `app.tool.result_anomalous` | Empty/null results feeding confident answers |
| Retried vs distinct side effects | `app.tool.retry_count`; distinct `app.tool.idempotency_key` | Retry loops multiplying writes |
| Cited-passage rank | Rank of the passage the answer cites | Never citing middle ranks → position bias (`agent-rag`) |

### Cost

- One versioned price table (input, cached input, output per model); compute cost in one
  place (Collector, span processor or backend).
- Uncached input = `input_tokens − cache_read`; price parts separately. Adding cache_read
  on top double-counts.
- Reasoning tokens usually bill as output; verify against current provider docs.
- Report quality at a cost: higher pass rate at double cost per task is a trade-off for
  the user, not a win.

## Dashboards

- Panels from the core metrics above, organised around `failure-taxonomy.md` categories
  and `design.md` success criteria; pass rates with CIs; "Other" query-cluster size for RAG.
- Segment every panel by `service.version`, prompt version, model and tenant tier.

## Alerts

Starting points; tune to your baseline.

| Alert | Trigger |
|---|---|
| Error rate | Root or tool error rate > 2× 7-day baseline for 15 min, or 5xx > 5% |
| Latency | p95 over the `design.md` budget for 15 min |
| Cost | Per task or per day > 1.5× baseline, or over budget |
| Loops | Any run over N LLM calls (N = step cap) |
| Quality | Online pass rate drops ≥ 5 points vs previous release, outside its CI |
| Feedback | Thumbs-down or edit rate > 2× baseline |
| Telemetry | Trace volume falls > 50% vs requests served |
| Ungated action | **Any** sensitive `execute_tool` without its gate span — P0, page now |
| Failover | Failover events above baseline, or any failover to an unevaluated model |

- Alert on relative change, never absolute judge scores — judges carry TPR/TNR bias. Read
  traces before acting.
- Every alert links to a saved query showing example traces.
- SLOs, paging and incident response: `agent-production`.

## Capturing user feedback

Signals, weakest to strongest:

1. Explicit thumbs/stars — sparse (often well under 1% of messages).
2. Behavioural: regenerate, copy, stop, abandon.
3. Conversational: the user rephrases or corrects.
4. **Outcome:** draft edited before sending, ticket closed, PR merged, answer accepted.

- **Return the trace or response ID with every answer**; the client sends it back with
  feedback. Without it feedback can't be joined.
- Attach feedback as a score on the trace or span it concerns; conversation-level signals
  on the session.
- Name scores after the signal (`draft_edited`, `thumbs_down`), not the hoped-for quality.
- Ask precisely: "Did we answer your question correctly?" over "Rate this response".
- Feedback givers are self-selected; users who left gave none.
- Prefer the signal closest to what the product is for.

This is the pack's home for feedback signals; `agent-evals` points here.

## Linking traces, evals and datasets

- Scores live on the evaluated span: `gen_ai.evaluation.result` (parented, or with
  `gen_ai.response.id`) or OpenInference `evaluation.*`/`annotation.*`. Judges, feedback
  and human labels use the same link.
- **Annotate the span holding the content.** Under OTel the root's I/O may be empty while
  content sits on a child LLM span; scoring the empty root is a common bug.
- Name scores after what they measure (`refusal`, not `refusal judge`); check judge
  filters so items aren't scored twice.
- Promote failing, flagged and negative-feedback traces to `datasets/` with provenance
  (trace ID, date, release, selection reason).
- Eval runs emit the same spans as production, tagged with dataset name and version.

## Hand-off to error analysis

Once `instrumentation-health.md` passes: sample ~100 traces, over-representing flagged,
low-score, latency/cost extremes and multi-turn sessions; `agent-evals` open-codes 30–50
(delegate to `trace-analyst`). Weekly until patterns stabilise, then monthly and after
incidents.

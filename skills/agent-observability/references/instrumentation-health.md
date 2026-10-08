# Instrumentation health

Loop: run the code path → fetch the real trace from the backend → audit → fix → repeat.
Run after first setup, adding a framework or service, upgrading an instrumentation or
SDK, and whenever a dashboard looks wrong.

## Smoke check — one fresh trace

Run one realistic request that uses at least one tool (and retrieval, if any):

- [ ] Exactly one trace; root is the agent span (`invoke_agent …` or AGENT/CHAIN).
- [ ] Root has curated input and output, and status OK or ERROR — not UNSET.
- [ ] Expected spans present: one LLM span per model call, TOOL, RETRIEVER, sub-agent.
- [ ] Tree intact: tools are children of the agent span; MCP server spans join the trace.
- [ ] LLM spans have model, tokens (cached, reasoning), finish reason, prompt name + version.
- [ ] Cost computed (span or backend).
- [ ] Tool spans carry arguments and results (or are redacted on purpose).
- [ ] Retrieval spans carry document IDs and scores.
- [ ] Conversation ID, user ID, release, environment set.
- [ ] A forced tool failure is an ERROR span with `error.type`, not only a log line.
- [ ] Seeded fake PII is redacted per policy.
- [ ] No secret anywhere in the trace.

## No trace arrived

| Cause | Check |
|---|---|
| Nothing emitted | Provider set before clients? Instrumentor called? Exited before flush? |
| Credentials | 401/403 in exporter or Collector logs |
| Network | Endpoint/protocol (gRPC 4317 vs HTTP 4318, path); proxy/TLS errors |
| Collector dropped | Payload too large, redaction/filter dropped everything, sampling |
| Indexing delay | Wait and re-query before changing code |

Add a console exporter next to OTLP to separate "not emitted" from "not delivered".

## Span-tree test (CI)

Run the agent against a stubbed model and assert the tree, so a loop refactor can't
silently break instrumentation.

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

def test_agent_emits_expected_tree(make_agent):         # stubbed model + tools
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    make_agent(tracer_provider=provider).handle_turn("conv-1", "user-1", "Where is order 1234?")
    spans = exporter.get_finished_spans()
    root = next(s for s in spans if s.parent is None)
    ops = [s.attributes.get("gen_ai.operation.name") for s in spans]
    assert root.name.startswith("invoke_agent") and root.status.status_code == StatusCode.OK
    assert "chat" in ops and "execute_tool" in ops
    assert len({s.context.trace_id for s in spans}) == 1           # no orphans
    for s in spans:
        if s.attributes.get("gen_ai.operation.name") == "chat":
            assert s.attributes.get("gen_ai.usage.input_tokens") is not None
```

TypeScript: `InMemorySpanExporter` + `SimpleSpanProcessor` from `@opentelemetry/sdk-trace-base`.

## Fleet checks — real traffic

Run over the last day or week of production traces.

| Check | Trigger | Usual fix |
|---|---|---|
| Orphaned spans | > 5% missing parent (≥ 5 traces) | Propagate context across async, threads, queues, services |
| Flat traces | > 80% of multi-step traces at depth 1 | Init tracing before clients; add agent root span |
| Uncategorised spans | Any AI span without a kind | Set `gen_ai.operation.name` / `openinference.span.kind` |
| Repeated names | Top 3 names > 95% of spans (avg > 3 spans/trace) | Descriptive low-cardinality names |
| Blank root I/O | > 25% of roots | Curated input/output on the root |
| Root status unset | > 80% UNSET | Set OK/ERROR explicitly or use decorators |
| Missing tokens | > 70% of LLM spans | Enable streaming usage, or set counts manually |
| Truncated traces | P10 ≤ 2 spans and P90 ≥ 8 | Tune batch queue/export size; truncate large attributes; flush |
| Duplicate LLM spans | > 20% duplicated | Remove a stacked instrumentor |
| Missing grouping IDs | > 5% of roots | Set conversation ID at entry |
| Missing versions | Any trace without release and prompt version | Resource attributes; prompt version at load |
| Trace volume gap | < 95% of requests (unsampled envs) | Flush, exporter errors, uninstrumented path |
| Errors only in logs | Error lines without an ERROR span | Record exceptions and set status |
| Ungated sensitive actions | Any sensitive `execute_tool` without gate span | Gate emits a span; block execution if it didn't run |

## Sabotage checks — prove detectors fire

A guard, validator, alert or flag that never fires looks identical to one that works —
silently no-op'ing checks go unnoticed for months. Feed each a known-bad input and confirm
it trips, emits its span or attribute, and (for alerts) reaches a human:

- injection string at the input guard; ungrounded answer at the grounding check;
- tool stub returning `null`/`[]` → `app.tool.result_anomalous` set;
- sensitive call bypassing the gate → P0 pages;
- synthetic cost or latency spike → budget alert.

Run in CI against stubs and periodically in staging/production with tagged synthetic
traffic. Record results and date (under "Verification" in `observability.md` if used).

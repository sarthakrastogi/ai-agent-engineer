# Instrumentation setup

## Debug-grade tracing

For seeing what the agent does right now. **Dev only** — it records full prompts, outputs
and tool arguments.

1. Console exporter, or a local backend (Phoenix, Langfuse, Jaeger) on `localhost`.
2. Content capture on.
3. Framework instrumentor from the table below; create clients after it.
4. Run one failing case and read the span tree top to bottom.

```python
import os
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "span_only"  # DEV ONLY
os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental")
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
# or OTLPSpanExporter() with OTEL_EXPORTER_OTLP_ENDPOINT=<local backend, port 4318>
trace.set_tracer_provider(provider)
# <FrameworkInstrumentor>().instrument(tracer_provider=provider), then create clients
```

**Before production, switch off:** content capture (or route it through redaction or an
external store, `content-capture-pii-sampling.md`); framework content defaults (OpenAI
Agents SDK `OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA=false`; AI SDK
`recordInputs`/`recordOutputs: false`); console export. Switch `SimpleSpanProcessor` →
`BatchSpanProcessor` with OTLP to a Collector; add `service.version`, sampling and the
health checks. Keep debug settings out of deploy config.

### Per-framework entry points

Verify against current provider docs; package names move. OpenInference instrumentors emit
OpenInference attributes — keep one schema per system.

| Framework | Entry point | Notes |
|---|---|---|
| LangGraph / LangChain | `openinference-instrumentation-langchain`: `LangChainInstrumentor().instrument()`; or `langsmith[otel]` + `LANGSMITH_OTEL_ENABLED=true` | `LANGSMITH_OTEL_ONLY=true` sends only to your OTLP endpoint |
| OpenAI Agents SDK | `openinference-instrumentation-openai-agents`: `OpenAIAgentsInstrumentor().instrument(tracer_provider=...)` | Traces to OpenAI by default with inputs/outputs; `add_trace_processor()` adds, `set_trace_processors()` replaces |
| Google ADK | `openinference-instrumentation-google-adk`: `GoogleADKInstrumentor()` | ADK also emits OTel natively |
| Anthropic SDK | `openinference-instrumentation-anthropic`: `AnthropicInstrumentor()` | LLM calls only; add root and tool spans |
| Claude Agent SDK | `openinference-instrumentation-claude-agent-sdk`: `ClaudeAgentSDKInstrumentor()` | |
| Vercel AI SDK (TS) | v7: `registerTelemetry(new OpenTelemetry())` from `@ai-sdk/otel`; v6: `experimental_telemetry: { isEnabled: true }`; Next.js: `registerOTel` from `@vercel/otel` | Records inputs/outputs by default; `@arizeai/openinference-vercel` for OpenInference |

JS equivalents are `@arizeai/openinference-instrumentation-<name>`.

## Order of operations

1. Tracer provider and exporter first.
2. Instrumentors next (framework, then provider).
3. Clients last — a client created before patching is never traced.
4. **App already has OTel:** add a processor/exporter to the existing provider. A second
   global provider is ignored or replaces the first; either way spans go missing.

## Auto vs manual

Preference: framework instrumentor → provider instrumentor → manual spans.

- Don't hand-roll spans an instrumentor emits; stacked instrumentors duplicate LLM spans.
- **Provider instrumentors capture the tool-call request, not execution or result.** Add
  manually: agent root, `execute_tool`, retrieval, rerank, guardrail, approval, sub-agent.
- Prefer decorators (`@observe`, `@mlflow.trace`, OpenInference `@tracer.tool`/`@tracer.agent`).
  Hand-rolled `start_as_current_span` never sets status OK, so roots end `UNSET` — set it.
- With decorators that capture arguments, **set trace input explicitly** to the user
  message, or configs, clients and API keys become the recorded input.

## Manual spans (shape)

```python
import os
os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental")
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import SpanKind, StatusCode

provider = TracerProvider(resource=Resource.create({
    "service.name": "support-agent", "service.version": os.environ["GIT_SHA"]}))
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))  # OTEL_EXPORTER_OTLP_ENDPOINT
trace.set_tracer_provider(provider)
# instrument providers here, then import/create clients
tracer = trace.get_tracer("support-agent")

def handle_turn(conversation_id: str, user_id: str, message: str) -> str:
    with tracer.start_as_current_span("invoke_agent support-agent", kind=SpanKind.INTERNAL) as root:
        root.set_attributes({"gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "support-agent", "gen_ai.agent.version": AGENT_VERSION,
            "gen_ai.conversation.id": conversation_id, "user.id": user_id})
        answer = run_loop(message)                  # chat spans come from the instrumentor
        root.set_status(StatusCode.OK)
        return answer

def run_tool(name: str, call_id: str, args: dict):
    with tracer.start_as_current_span(f"execute_tool {name}", kind=SpanKind.INTERNAL) as s:
        s.set_attributes({"gen_ai.operation.name": "execute_tool",
                          "gen_ai.tool.name": name, "gen_ai.tool.call.id": call_id})
        try:
            tool = TOOLS[name]; result = tool(**args)
            s.set_status(StatusCode.OK); return result
        except Exception as e:
            s.record_exception(e); s.set_attribute("error.type", type(e).__name__)
            s.set_status(StatusCode.ERROR); raise
```

TypeScript: `NodeSDK` from `@opentelemetry/sdk-node` with `OTLPTraceExporter`, started in
a module imported before any LLM client; `tracer.startActiveSpan(...)` with the same
attributes, status and `span.end()` in `finally`.

## Export: OTLP to a Collector

- The app knows only `OTEL_EXPORTER_OTLP_ENDPOINT`; the Collector fans out to backends
  (Langfuse, Phoenix, LangSmith, Braintrust, MLflow, Datadog, Grafana, Honeycomb — pick by
  what the team runs). Redaction and tail sampling live there too.
- Direct-to-backend is fine for a prototype; move to a Collector before production.

```yaml
receivers:  { otlp: { protocols: { http: {}, grpc: {} } } }
processors: { batch: {} }            # add redaction / tail_sampling here
exporters:
  otlphttp/llm_backend: { endpoint: "<llm-backend-otlp-url>", headers: { Authorization: "${env:LLM_BACKEND_AUTH}" } }
  otlphttp/apm:         { endpoint: "<apm-otlp-url>" }
service:
  pipelines:
    traces: { receivers: [otlp], processors: [batch], exporters: [otlphttp/llm_backend, otlphttp/apm] }
```

## Context propagation

- `contextvars` / `AsyncLocalStorage` carry context across `await`. **Thread pools and
  worker callbacks don't** — wrap work in a copied context or use threading instrumentation.
- Across services and queues: inject W3C `traceparent` into headers or message attributes;
  extract on the consumer. Background jobs link to the originating turn.
- MCP: `params._meta` (`span-model-and-semconv.md`).
- Agent-to-agent handoffs: extract on the way in, inject on the way out, so the receiver
  joins the caller's trace.
- Carry the pseudonymous end-user ID through every hop (e.g. `baggage` copied onto each
  root span) so "which action, on whose authority" is answerable downstream. No raw PII in
  baggage.

## IDs and versions on every trace

| What | Attribute |
|---|---|
| Conversation / session | `gen_ai.conversation.id` (OpenInference `session.id`) on root and LLM spans |
| User (pseudonymous) | `user.id` on root; hash if policy requires |
| Agent, prompt version | `gen_ai.agent.version`, `gen_ai.prompt.name` / `.version` |
| Model requested vs served | `gen_ai.request.model`, `gen_ai.response.model` (catches alias moves) |
| Release, environment | `service.version` (git SHA), `deployment.environment.name` |
| Feature / tenant tier | `app.*` |

- Backends map session/user keys differently; set both the OTel and backend key if needed.
- **Structured logs carry the trace ID** on every line. Traces show model behaviour; logs
  and attributes show app decisions (cache hit, route, validation result).
- Return the trace ID to the client with each answer for feedback joins.

## Flush before exit

Scripts, CLIs, notebooks, serverless and eval runners exit before the batch processor
sends: `force_flush()` then `shutdown()` (Python), `await sdk.shutdown()` (Node).

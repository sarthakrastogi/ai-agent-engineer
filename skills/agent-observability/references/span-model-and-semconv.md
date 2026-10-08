# Span model and semantic conventions

Verify attribute names against the current GenAI semconv (`semantic-conventions-genai`
repo) and each instrumentation's README before relying on them.

## Status

- GenAI semconv is **Development** status; names change between releases
  (`gen_ai.system` → `gen_ai.provider.name`; token metrics histogram → counters).
- Instrumentations emit old conventions unless you set
  `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` (some have their own opt-in).
- Record the semconv version and opt-in (`observability.md` if used).

## Choosing a schema

| Option | Pick when |
|---|---|
| **OTel GenAI semconv** (default) | Vendor-neutral; general APM backends must understand spans |
| **OpenInference** | Backend is Phoenix/Arize, or the best instrumentor for the stack emits it (still valid OTLP) |
| Vendor SDK only | Never as the only layer |
| Third-party agent platform | Require OTLP (or equivalent) export of step-level model calls, tool calls and cost before adopting |

One schema per system, in every service. Mixed schemas break cross-service queries and
judges that read specific attributes.

## Span hierarchy

One trace per user turn or task; turns grouped by conversation ID.

```
invoke_workflow <name>            multi-agent orchestrators only
└─ invoke_agent <agent.name>      root; INTERNAL in-process, CLIENT if remote
   ├─ plan                        optional
   ├─ chat <model>                CLIENT; one span PER model call
   ├─ approval <tool.name>        INTERNAL; gate before a sensitive tool
   ├─ execute_tool <tool.name>    INTERNAL; sibling of the chat span that requested it
   │   └─ MCP client span → MCP server span (context in params._meta)
   ├─ retrieval <data_source.id>  CLIENT
   ├─ embeddings <model>          CLIENT
   └─ invoke_agent <sub-agent>    sub-agent typed as an agent, not a tool
```

- Names are low-cardinality: `{operation} {model}`, `execute_tool {tool.name}`,
  `retrieval {data_source.id}`, `invoke_agent {agent.name}`. IDs and user values go in
  attributes.
- One span covers all retries of a logical operation; retries are attributes or children.
- Tools and sub-agents are siblings of the generation that requested them, under the agent.
- **Approval gate emits its own span** (decision, approver, policy), so a sensitive
  `execute_tool` without one is detectable.
- **Provider/model failover is an event**: `app.failover.{from,to,reason}` on the inference
  span.
- **MCP:** propagate W3C `traceparent`/`tracestate`/`baggage` unprefixed in the request's
  `params._meta`; HTTP headers don't cover individual JSON-RPC messages.
- `gen_ai.operation.name` values: `chat`, `generate_content`, `text_completion`,
  `embeddings`, `retrieval`, `execute_tool`, `create_agent`, `invoke_agent`,
  `invoke_workflow`, `plan`, memory ops such as `search_memory`.

## Key OTel GenAI attributes

| Span | Always set | Recommended | Opt-in content |
|---|---|---|---|
| Inference (`chat`) | `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.conversation.id`, `gen_ai.prompt.name` / `.version`, `error.type` on failure | `gen_ai.response.{model,id,finish_reasons}`, `gen_ai.request.{temperature,max_tokens,reasoning.level}`, `gen_ai.usage.{input_tokens,output_tokens,cache_read.input_tokens,cache_write.input_tokens,reasoning.output_tokens}` | `gen_ai.system_instructions`, `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.tool.definitions` |
| Tool (`execute_tool`) | `gen_ai.tool.name` | `gen_ai.tool.call.id`, `gen_ai.tool.type`, `gen_ai.tool.description` | `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result` |
| Retrieval | `gen_ai.operation.name`, `gen_ai.data_source.id` | `gen_ai.retrieval.top_k` | `gen_ai.retrieval.query.text`, `gen_ai.retrieval.documents` |
| Agent (`invoke_agent`) | `gen_ai.operation.name` | `gen_ai.agent.{id,name,description,version}`, `gen_ai.conversation.id` | — |

- **`gen_ai.usage.input_tokens` already includes cached tokens.** Don't add
  `cache_read` on top; subtract it to price cached tokens separately.
- Set operation, provider and model **at span start** so samplers see them.
- Own attributes go under `app.*` (`app.rerank.model`, `app.tenant.tier`); never invent
  `gen_ai.*`.
- **Tool spans also carry:**
  - `app.tool.idempotency_key`, `app.tool.retry_count` on side-effecting tools — separates
    distinct requests from one request multiplied by a retry loop.
  - `app.tool.result_anomalous=true` when a result is empty, `null`, truncated or
    error-shaped without raising — the model answers confidently from these and nothing
    else flags them.
  - `app.tool.error_class=recoverable|hard_blocker` on failures, matching the tool's
    triage (`agent-tools` → `references/tool-responses-and-errors.md`). Retried hard
    blockers = wasted budget; escalated recoverables = lost autonomy.

## OpenInference equivalents

| Concept | OpenInference |
|---|---|
| Span type | `openinference.span.kind` = LLM, EMBEDDING, CHAIN, RETRIEVER, RERANKER, TOOL, AGENT, GUARDRAIL, EVALUATOR, PROMPT, DECISION (required) |
| Input / output | `input.value`, `output.value` (+ mime type) |
| Model, messages | `llm.model_name`, `llm.input_messages.{i}.message.*`, `llm.output_messages.*` |
| Tokens, cost | `llm.token_count.{prompt,completion,total}`, `llm.cost.*` |
| Prompt version | `llm.prompt_template.version` |
| Tool | `tool.name`, `tool.description`, `tool.parameters` |
| Retrieval | `retrieval.documents.{i}.document.{id,content,score}`, `reranker.*` |
| Grouping | `session.id`, `user.id` |
| Scores | `evaluation.*`, `annotation.*` |

Under OTel GenAI, model rerankers and guardrails as INTERNAL spans with `app.*` attributes.

## GenAI metrics

- Histograms: `gen_ai.client.operation.duration`, `gen_ai.client.operation.time_to_first_chunk`,
  `gen_ai.invoke_agent.duration`, `gen_ai.invoke_agent.inference_calls`,
  `gen_ai.invoke_agent.tool_calls`, `gen_ai.execute_tool.duration`.
- Tokens: counters `gen_ai.client.inference.usage.*_tokens` for totals and cost. Older
  instrumentations emit the `gen_ai.client.token.usage` histogram instead — check which
  before building dashboards.

## Evaluation event

`gen_ai.evaluation.result` with `gen_ai.evaluation.{name,score.value,score.label,explanation}`.
Parent it to the evaluated span, or set `gen_ai.response.id` when evaluation runs later in
another process.

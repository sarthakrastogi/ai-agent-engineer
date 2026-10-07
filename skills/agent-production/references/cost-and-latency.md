# Cost and latency

## Measure first

| Metric | Definition |
|---|---|
| Cost per successful task | Token cost of every call in the task (agent, subagents, judges, retries) ÷ tasks that passed |
| Cache hit rate | Cached input tokens ÷ all input tokens (Anthropic: `cache_read_input_tokens` ÷ (`cache_read` + `cache_creation` + `input_tokens`); OpenAI: `cached_tokens` ÷ prompt tokens) |
| End-to-end latency | p50/p95/p99 per task (root span), not per call |
| TTFT | Request to first streamed token the user sees (client-side) |
| Calls and tokens per task | LLM calls, tool calls, input/output tokens |

- Optimise cost per **successful** task: a cheaper model that fails more or takes more turns
  can cost more.
- Report quality at a cost and latency, never alone.
- Agents use ~4× the tokens of chat, multi-agent ~15×. Check the task value justifies it.
- Find the dominant term from traces (input vs output, LLM vs tool time) before acting.
- Model cost per task from its drivers (for a coding agent: files modified, tools used,
  exploration depth), so a task-mix shift explains a cost change before you blame the model.

## Levers

| Lever | Saves | Verify | Watch |
|---|---|---|---|
| Prompt caching | Input cost (reads ≈ 0.1× base), some latency | Cache-read tokens > 0 on 2nd call | Silent miss below min length; prefix churn |
| Effort / reasoning level | Output tokens, latency | Eval sweep across levels | Quality cliffs on hard cases |
| Smaller model / routing | Cost, latency | Per-route evals | Misrouted hard cases |
| Batch API | ~50% | Completion time vs SLA | Up to 24 h turnaround |
| Fewer output tokens | Latency (≈ proportional) | p50/p95 | Over-terse answers |
| Streaming | Perceived latency | TTFT | Output guards must buffer or retract |
| Parallel tool calls / subagents | Wall-clock (up to ~90% on research) | p95 | More tokens; write conflicts |
| Token budgets | Runaway cost | Cap-hit rate | Truncation (`length` finish reason) |

## Prompt caching

Usually the biggest lever: agent loops run ~100:1 input to output. Cache writes cost more
than base input (Anthropic: 1.25× for 5-min TTL, 2× for 1-h), so a prefix must be reused to
pay off. Count reads and writes in cost per task; alert when hit rate drops after a deploy.
Verify against current provider docs. Layout and mechanics: `agent-context` →
`references/prompt-caching.md`.

## Model choice, effort and routing

1. Baseline on the most capable model at full effort (quality ceiling).
2. Sweep effort on that model; often a better lever than switching models.
3. Try smaller models per step where evals hold. Hot-path calls with bounded output
   (query parsing, classification, routing) on every request are candidates for a small
   fine-tuned or open-weight model, gated on the same evals. Fine-tune for behaviour, never
   to add knowledge.
4. Only then multi-model (routing, cascade, orchestrator–workers; shapes in `agent-design`
   → `references/model-and-framework-choice.md`). Evaluate each route; the router must cost
   far less than it saves (an LLM router adds 1–5 s), so use code or a small classifier
   (decision-classifiers.md); the setup must beat the single model's effort/cost curve.

## Batching

For backfills, nightly evals, bulk enrichment. Use the 1-hour cache TTL since batch requests
may run far apart.

## Latency

- Output dominates: halving output ≈ halves latency; halving input saves 1–5%.
- Stream for sub-second TTFT; show progress on tool steps.
- Merge sequential calls that always run together; parallelise independent ones (prompt it:
  "make all independent tool calls in parallel"); run guards or retrieval alongside
  generation when nothing depends on them.
- Agentic RAG with 3–10 queries per request waits on the slowest: budget the vector store's
  p99, keep indexes warm after deploys and scale-ups.
- Don't call a model when code will do: hard-coded confirmations and refusals, pre-computed
  small input spaces.
- Auth, rate limits, input-size limits and exact-match cache lookups run before the agent
  framework is invoked.

## Simplify after hitting the target

Optimise against a floor ("keep > 94%, minimise cost"), using the eval suite:

- Ablate one component at a time (skip verification, 5 chunks not 10, drop a tool); keep
  the cut if quality stays above the floor.
- Make rare-need steps conditional (a search used in 30% of runs shouldn't run in 100%).
- Merge steps that always run together into one structured call.
- If one path is taken ~90% of the time, make it the default in code.
- Downgrade the model per step where traces show execution, not reasoning.
- Profile first: one slow sequential call often dominates.

## Token budgets

- Set `max_tokens` per call deliberately (includes thinking on reasoning models); a rising
  `length` finish-reason rate means truncation.
- Cap and paginate tool output (`agent-tools`).
- Cap tokens and spend per run and per tenant per day; stop with saved state.
- Compact long runs (`agent-context`).

## Don't

- Semantic caching of answers: similar queries get wrong answers. Cache by ID or exact,
  constrained inputs.
- Compare costs on a handful of prompts; use the eval set and the same success criteria.

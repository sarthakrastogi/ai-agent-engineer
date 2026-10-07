# Model and framework choice

Vendor names are options, not recommendations. Verify model IDs, effort parameters and
prices against current provider docs.

## Framework vs raw SDK

Start with the raw API; the patterns in `workflow-patterns.md` are a few lines of code, and
wrong assumptions about framework internals are a common source of bugs. Whatever you choose,
own your prompts, context window and control flow.

Things that prevent work run in plain code before the agent is invoked: auth, rate limits,
input-size limits, exact-match cache checks. Things that are work go inside it.

| Situation | Choose |
|---|---|
| Single call, routing, short chains | Raw SDK + structured outputs |
| Agent loop with a handful of tools, short runs | Raw SDK loop or a thin vendor agent SDK |
| Long runs, approvals that wait hours, crash recovery | Durable execution (workflow engine or framework with checkpointing): the strongest reason to adopt one |
| Multi-agent with handoffs and shared state | Framework with explicit graphs/handoffs and tracing, after passing `multi-agent.md` checks |
| Team already standardised on a framework | Use it if it passes the checklist |
| Frequent provider switches | Thin abstraction layer that keeps caching, thinking and similar features reachable |

### Framework checklist

Reject the framework (or how you use it) if any answer is "no":

- [ ] Can you see the exact prompt, tool definitions and messages on every call?
- [ ] Can you edit the system prompt and tool descriptions directly, as versioned files?
- [ ] Can you control the loop: cap turns, interrupt for approval, compact, resume?
- [ ] Does it emit or export traces for LLM calls, tool calls and handoffs (`agent-observability`)?
- [ ] Can it checkpoint and resume after a crash or a human wait (`agent-production`)?
- [ ] Can it mix deterministic steps and autonomy in one flow?
- [ ] Does it expose provider features you rely on (caching, reasoning effort, structured
      outputs, strict tools)?
- [ ] Can you run your eval suite against it without a hosted service?

Options: provider SDKs; vendor agent SDKs (Claude Agent SDK, OpenAI Agents SDK, Google ADK);
graph frameworks (LangGraph, Pydantic AI, CrewAI, LlamaIndex workflows); durable execution
(Temporal, Inngest, cloud step functions) around raw SDK calls.

## Model selection

1. **Baseline every LLM step on the most capable model** at generous reasoning effort. This
   proves solvability and sets the ceiling. Don't start small before you know it can be done.
2. **Build the eval first** (`agent-evals`), 20–50 real cases. Order: evals → accuracy target
   → cost and latency.
3. **Sweep effort before switching models.** Run the eval at each effort level; plot
   accuracy vs cost per task. Effort is often a better lever than model choice.
4. **Step down per step.** Try a smaller model on each step; keep it where the eval holds
   within the agreed margin. Routing, extraction and classification step down first;
   planning and synthesis last. Small or open-weight models qualify on the same eval.
5. **Multi-model only after the sweep**, and only if it beats the single model's full
   effort/cost curve.
6. **Record** pinned snapshot IDs (not aliases), effort settings, eval result and reason in
   `design.md`. Track retirement dates.

Start efficiency-first (small model, low effort) only for simple, high-volume
classification or extraction where latency dominates.

### Multi-model patterns

| Pattern | Shape | Use when | Caveat |
|---|---|---|---|
| Routing by difficulty | Classifier sends easy inputs small, hard ones large | Difficulty is detectable up front | Measure router accuracy; misroutes cost quality |
| Advisor | Cheap executor consults a frontier model on hard decisions | Serial work hard only in spots | Fails if consults collapse; prompt for 2–3 per task |
| Orchestrator | Frontier coordinator + cheap parallel workers | Independent bulk work | ~50% cheaper, several times faster, ~12 points less accurate |
| Single model, lower effort | One model throughout | Dependent chains | Usually 20–30% cheaper than multi-model here |
| Small checker | Small model screens inputs, verifies outputs, flags low confidence | High volume, fast gate before an expensive call | Validate the checker like a judge (`agent-evals`) |

### Cost and latency

- Output tokens dominate latency: halving output roughly halves latency; halving input saves
  1–5%.
- Measure **cost per task**, not per token: a cheaper model needing more turns can cost more.
- Caching, batching, streaming: `agent-production`.

### Changing models later

A model change is a behaviour change: rerun the full eval, redo the effort sweep, remove
over-prompting written for the weaker model, re-baseline cost and latency, log it in
`experiment-log.md` (`agent-production` → `references/model-migration.md`).

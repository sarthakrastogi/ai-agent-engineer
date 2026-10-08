# Workflow patterns

Patterns compose: a router can send one branch to a chain and another to an agent. Make
every edge that can be a code check a code check.

## Choosing

| Pattern | Use when | Cost / latency vs single call |
|---|---|---|
| Single call | One input → one output; knowledge fits in prompt or retrieval | 1x |
| Prompt chaining | Fixed, separable subtasks; you want to inspect intermediates | N calls, serial |
| Routing | Distinct input categories; easy ones can go to a small model | ~1x + cheap classifier |
| Parallelisation | Independent subtasks (sectioning) or several attempts (voting) | N calls, parallel |
| Orchestrator-workers | Subtasks unknown until the input is seen | Variable |
| Evaluator-optimizer | Clear criteria; critique measurably improves output | 2–3x per round |
| Agent loop | Path depends on intermediate results | Unbounded unless capped (`multi-agent.md` → Cost) |
| Plan-then-execute | Real side effects users must approve first | + read-only pass and a human wait |

- Pick the cheapest row that meets the success criteria on the eval set.
- Before any LLM step, ask whether code can do it.
- Count **evaluation burden** as a cost: a workflow is testable per node and route; an agent
  needs end-to-end trajectory evals. Choose the agent loop only when tool selection can't be
  anticipated or the paths are too many to maintain as a graph.

## Pitfalls by pattern

| Pattern | Non-obvious rule | Pitfalls |
|---|---|---|
| Single call | Try it first and measure; usually enough for classification, extraction, Q&A over given text | Skipping it because it feels too simple; stuffing the prompt instead of retrieving |
| Prompt chaining | A **code gate** between steps stops or retries early | No gates, so one bad step poisons the rest; passing full history instead of what the next step needs |
| Routing | Code or rules for exact categories; LLM with enum output only for semantic ones | No `other` route; router accuracy never measured on its own; overlapping categories that route differently on reruns |
| Parallelisation | Aggregate in code (majority, any-flag, threshold) | Sections that aren't independent; a parallel guardrail that fires after side effects |
| Orchestrator-workers | Orchestrator plans as structured output; code dispatches and caps subtasks | One-line briefs (use the delegation brief in `multi-agent.md`); workers returning transcripts |
| Evaluator-optimizer | Prefer deterministic evaluators (tests, linters, schemas); cap rounds, then escalate | LLM evaluator never validated against human labels (`agent-evals`); criteria broader than requirements; oscillation |
| Agent loop | Your code owns the loop so it can interrupt for approval or compaction; essentials in `the-agent-stack.md` | No turn cap; no runnable verification, so it stops "when it looks done"; errors hidden from the model; focused runs past ~10–20 steps without decomposition |

**The router must cost less than it saves.** An LLM router adds 1–5 s, doubling short
requests. Prefer code or a small classifier with an `other` route and a confidence score;
send low confidence (threshold measured on labelled data) to a human or the general handler
(`agent-production` → `references/decision-classifiers.md`). If one route takes ~90% of
traffic, make it the default in code and classify only the rest.

**A parallel guard must block before any side effect** (`agent-guardrails`); running it
beside the answer is fine only if nothing acts until it returns.

**Agent loop exits are explicit:** final-output tool or schema, no tool call, unrecoverable
error, turn cap, cost cap. Rejected approvals go back into context so the model sees them.

## Plan-then-execute

- **When:** the agent writes files, runs migrations or deploys, and users must see what will
  happen first, or the request is ambiguous.
- **Enforce plan mode in code:** the plan pass gets read-only tools only; execute gets write
  tools and follows the approved plan; deviations go back to the user.
- **Pitfalls:** plan mode enforced only in the prompt; plans too vague to check execution
  against; re-planning every turn on small tasks.

## Human approval gate

- **When:** before high-risk actions (irreversible, financial, external messages, shared
  systems), on repeated failures, on out-of-scope requests.
- **Shape:** "contact a human" is a tool. On a gated call, persist run state, notify, stop
  using compute, resume on approve/reject (SDK interruption + serialised state, or a
  durable-execution wait step).
- **Pitfalls:** approvals on low-risk calls (fatigue); UI hiding the exact arguments;
  resuming from client-supplied state; the LLM deciding whether approval is needed.

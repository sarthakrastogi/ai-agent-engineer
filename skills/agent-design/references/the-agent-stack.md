# The agent stack

Each layer contains the one below. No layer replaces the one below: a graph of loops still
fails if one prompt is wrong.

| # | Layer | What you engineer | Fixes failures like… | Owning skill |
|---|---|---|---|---|
| 1 | Prompt | Wording, structure, examples, output format of one request | Right facts in view, wrong wording, format or tone | `agent-prompting` |
| 2 | Context | What the model sees per call: retrieved docs, history, tool definitions, memory, state | The model didn't see the right facts or tools | `agent-context`, `agent-rag` |
| 3 | Harness | Tools, filesystem, code execution, sandbox, memory, compaction, verification, permissions | No safety rail, no verification, state lost between runs | `agent-tools`, `agent-guardrails`, `agent-context` |
| 4 | Loop | Goal, iteration, error triage, stop condition | Runs forever, stops early, retries the same mistake | this skill, `agent-production` |
| 5 | Graph | Nodes (agents, tools, code, humans) with declared edges and handoffs | Roles collide, handoffs lose work, no one owns the output | this skill (`multi-agent.md`) |

## Diagnose

Ask in order: is it the **wording**, the **missing context**, the **missing safety rail**,
the **missing stop condition**, or the **missing org chart**?

1. Read 10–20 failing traces before naming a layer (`agent-evals` error analysis).
2. Fix at the **lowest** layer that explains the failure. A context failure patched with
   prompt wording comes back; a loop failure patched with a graph gets worse.
3. Climb only when the layer below is sound and the eval still fails for a reason the higher
   layer addresses. Write that reason in the decision log.
4. Don't skip layers: a graph needs working loops; a loop needs a harness with verification.

Most tasks never need a graph: a well-contexted prompt inside a decent harness is a correct
production design.

## Stack vs ladder

| Ladder rung | Stack shape |
|---|---|
| Single call | Prompt + context, minimal harness |
| Workflow | A declared graph of single calls and code: you fix the path |
| Single agent | One loop inside a harness: the agent picks the path |
| Multi-agent | A graph whose nodes are loops |

Known path → declared graph with deterministic edges beats a loop. Unknown path → one bounded
loop beats a multi-agent graph. Work touching money, data or customer trust → declared graph
with validation steps and human checkpoints.

## Layer notes

- **Prompt:** controls what you ask, not what the model sees. A perfect prompt over the wrong
  documents is a layer-2 failure.
- **Context:** a curation step before every call, not a prompt written once. Retrieve broad,
  re-rank to a precise top-k; load the minimal tool set; fetch on demand instead of preloading.
- **Harness:** invest here; it survives model upgrades, prompts don't. A model cutting corners
  as its window fills is a harness problem, not a prompting one. Models can overfit to a
  harness, so re-evaluate harness choices on model migration (`agent-production`).
  **Design verification first**, then build the generator to produce verifiable output; a
  failing test is the most actionable signal.

## Loop essentials

Every loop needs these before it ships:

1. **A concrete, observable goal.** Not "handle the support queue better" but "resolve
   battery tickets by checking diagnostics, offering a fix, escalating only if capacity
   < 80%".
2. **A termination condition:** success check, final-output tool, turn cap, cost cap.
3. **Error triage.** Recoverable errors (bad syntax, missing field) go back to the model with
   an actionable message. Hard blockers (missing credentials, undefined case) stop and
   escalate at once (`agent-tools` → `references/tool-responses-and-errors.md`). Consecutive-
   error thresholds: `agent-production` → `references/reliability.md`.
4. **Small actions with reliable observations:** each step yields evidence (tool result,
   test run) the next can act on.
5. **Failure feedback:** pass what was tried and how it failed into the next attempt. Feeding
   verification failures back beats single-shot generation by a wide margin.
6. **A retry ceiling that surfaces work:** after the cap, stop, show what was tried, ask.

Shapes: `workflow-patterns.md`. Multi-window runs: `agent-context` →
`references/long-running-agents.md`. Scheduled loops: `agent-production`.

## When a graph is justified

Loop vs graph is who decides the path: in a loop the agent picks the route; in a graph you
declare valid paths and the checks along them. Design per graph: role definitions (domain
and tools per node), handoff formats (`multi-agent.md` delegation brief), and the logic that
decides which nodes run, in what order, and where parallelism is safe.

**The trap:** replacing a debuggable loop with a multi-agent graph where every decision
becomes a sequential LLM call. Typical result: lower accuracy, opaque failures, long waits.
The shape that works concentrates intelligence: a cheap model routes and selects inputs, a
strong model generates, deterministic checks verify.

Use a graph only when one holds, and record which (in `design.md` if used):

- **Roles diverge:** different tools, permissions or knowledge per node.
- **Steps are truly independent** and can run in parallel.
- **Handoffs must be auditable:** first try a declared graph of code and single calls that
  logs each intermediate.

Make every edge that can be a code check a code check, and run `multi-agent.md` checks before
any node becomes its own agent.

## Constrain before you climb

Before adding a layer, narrow the output space: one target stack, schema or format to tune
and evaluate against. An agent that can generate anything generates inconsistent things.

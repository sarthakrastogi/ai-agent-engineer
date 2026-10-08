# Multi-agent systems

Default: one agent with good tools and context management. Most "we need multi-agent"
problems are tool overlap (`agent-tools`), long-run degradation (`agent-context`) or
sprawling prompt logic (`agent-prompting`). Diagnose lower stack layers first
(`the-agent-stack.md`).

## When it helps vs hurts

| Helps | Hurts |
|---|---|
| Many independent reads (research, multi-source search, review of independent files) | Parts that share context or have dependencies (most coding) |
| Information exceeding one context window | Several agents writing parts of one artefact |
| Many complex tools that split cleanly by domain | Low-value or latency-sensitive tasks |
| Fresh-context review, unbiased by having written the work | Tasks a single agent already passes |

**Parallelise reads, keep one writer.** Actions carry implicit decisions; parallel writers
make conflicting ones. Research fans out; synthesis and edits stay in one agent.

## Cost

- Agents ~4x chat tokens; multi-agent ~15x, so ~4x a single agent.
- Token spend explains most of the performance gain. Compare against a single agent **given
  the same token budget**.
- Best case (breadth-first research, strong lead + cheaper workers, 3–5 parallel workers):
  large quality gains and up to ~90% less wall-clock.
- Coordination channels grow as n(n−1)/2; each is a latency and failure point. Sequential
  agent calls compound latency.

Estimate `tasks/day × (lead tokens + workers × worker tokens) × price` (in `design.md` if
used). If task value doesn't cover that, don't split.

## Checks before splitting

Answer each (in `design.md` if used). Split only if 1 and 2 are "yes" and the rest are
handled.

1. Does a single-agent baseline fail the eval for a reason splitting fixes (context overflow,
   domain tool confusion, wall-clock), not one better tools or prompts would fix?
2. Can each subtask run without the others' intermediate work?
3. Does exactly one agent (or code) write the final output or take actions?
4. Is token cost affordable at expected volume?
5. Can one trace show every agent's prompts, tool calls and handoffs?
6. Are subagent count and per-subagent turns capped?

## Topologies

| Topology | Shape | Use when |
|---|---|---|
| Manager (agents-as-tools) | One agent owns the conversation, calls specialists as tools | Default: one voice, central control |
| Orchestrator + parallel workers | Lead plans, spawns clean-context workers, synthesises | Breadth-first research, bulk independent analysis |
| Decentralised handoff | Control and conversation transfer to a peer | Triage where the specialist takes over entirely |
| Hierarchical | Supervisors over specialist groups | Very large tool/domain surfaces; every level adds a handoff to trace and eval |
| Pipeline of agents | Fixed sequence of agents | Rarely right; use prompt chaining with agent steps |

## Delegation brief

One-line tasks get misread and duplicated. Every delegation carries:

```text
Objective:     what to find or produce, and why it matters to the parent task
Output:        exact format and length (e.g. ≤ 1,500-token summary + file paths)
Tools/sources: which to use, which to avoid
Boundaries:    what is out of scope; what other workers cover
Budget:        max tool calls / turns
```

Put scaling rules in the lead's prompt: fact-finding = 1 agent, 3–10 calls; comparisons =
2–4 subagents, 10–15 calls each; complex research = 10+ subagents. Current models
over-spawn: tell the lead to delegate only parallel, isolated work and do sequential or
single-file tasks itself.

## Isolation and handoff

- Workers return a distilled summary (~1,000–2,000 tokens), not their transcript.
- Write large outputs to files or a store; pass references (paths, IDs), not content.
- If workers' decisions interact, share the full trace of prior decisions, not just the
  final message.
- Conversation handoffs transfer the state the next agent needs explicitly.

## Coordination caveats

- A synchronous lead waits for the slowest worker and can't steer; async is faster but
  harder to debug and checkpoint.
- Small lead-prompt changes shift worker behaviour unpredictably: trace agent-to-agent
  interactions and eval the system end to end.
- Judge the end state, not whether agents followed the expected path; start with ~20 real
  cases.
- Make each worker resumable and tell the lead when one fails (`agent-production`).

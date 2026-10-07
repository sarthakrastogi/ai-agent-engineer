# Memory and compaction

## The four levers

| Lever | Means | Techniques |
|---|---|---|
| **Write** | Save outside the window | Scratchpads, todo/progress files, memory stores |
| **Select** | Pull in only what the next step needs | Memory retrieval, tool search, just-in-time reads, RAG |
| **Compress** | Shrink what stays | Tool-result clearing, compaction, trimming |
| **Isolate** | Separate window | Subagents, sandboxes, state fields hidden from the model |

Use the lightest that works: clearing → compaction → notes → isolation.

## Tool-result clearing

Old tool outputs are usually the largest, least useful part of history.

- **Keep the call, replace the payload** with a stub and pointer: `[cleared: 412 lines of
  search results, re-run search_logs(q="timeout", since=…) or read /tmp/r17.json]`.
- **Keep the last few results in full** (e.g. trigger at 100K tokens, keep the last 3).
- **Clear in chunks** large enough to pay for the cache miss each clear causes.
- **Exempt results that must persist** (fetched spec, the user's requirements).
- **Warn the model before clearing** so it can save what matters.
- Use the provider's context-editing feature if offered (Anthropic `clear_tool_uses` with
  `clear_at_least`, `exclude_tools`); otherwise implement the policy in context assembly.

## Compaction

For long conversational back-and-forth where clearing isn't enough.

- **Prefer provider server-side compaction** (Anthropic: `compact_*` edit in
  `context_management`; the SDK `compaction_control` is deprecated). Building your own:
  trigger on a token threshold, not a turn count.
- **Chat default:** keep the last ~10 turns verbatim, summarise older ones. Never
  blind-trim to the last N; a constraint stated earlier silently disappears.
- **Give the compactor a must-preserve list:**

```text
Summarise the conversation so far for your own continuation. Preserve exactly:
- the user's goal and every explicit constraint or preference
- decisions made and why; options rejected and why
- every file path, ID, URL and command touched, with its current state
- open questions, failing tests and the next planned step
- errors hit and what was learned from them (not resolved noise)
Drop: raw tool output already acted on, superseded plans, pleasantries.
Mark anything unverified as UNVERIFIED.
```

- **Restorable:** drop content, keep the path, URL or query that regenerates it.
- **Mark compaction in telemetry** (`gen_ai.conversation.compacted`) to check quality after
  compaction events.
- **Purge poisoned facts:** before a summary becomes ground truth, drop claims no tool
  result supports.
- **Tell the agent compaction exists**, or a window-aware model takes shortcuts near the
  limit: "Your context will be compacted automatically. Do not stop tasks early due to
  token budget concerns. Save your current progress to memory before the window
  refreshes."
- **After two failed corrections**, start fresh with a better brief.

## Errors stay in context

- **Leave failed actions and their errors in** so the model doesn't repeat them.
- **Collapse once resolved** into one line ("tried X, failed because Y, fixed with Z").
- **Count consecutive errors** and escalate past a threshold (`agent-production` →
  `references/reliability.md`).
- **Make error text actionable** at the tool (`agent-tools`).

## Scratchpads and notes

- **Give the agent a place to write** (file, state field or memory tool) for plans,
  findings and decisions outside the history.
- **Format by data type:** JSON for structured state (task lists, test status) — models
  overwrite it less than Markdown; free text for notes; git for checkpoints.
- **Recite the plan:** the agent rewrites `todo.md` (goal, done, next) as it goes, keeping
  the goal in recent attention. Use on tasks of ~50+ tool calls.
- **Summarise finished phases** into notes and drop their detail.

## Long-term memory

Add only for a real user need (preferences, prior decisions, learned procedures). Every
store is also a persistence channel for bad data.

| Type | Holds | Retrieval |
|---|---|---|
| Semantic | Facts about user, account, domain | Key lookup or embedding search, scope-filtered |
| Episodic | Past interactions, worked examples | Similarity to current task, used as few-shot |
| Procedural | Learned instructions or rules | Loaded into system prompt or a skill file; changed under review |

- **Explicit read/write tools** (`memory_view`, `memory_write`, or a file directory) so
  writes show in traces. No silent background extraction.
- **Scope every record** by tenant, user and agent, enforced in code.
- **Provenance and time on each record:** source turn/trace ID, author (user, agent, tool),
  date. Prefer recent; expire stale.
- **Memory is untrusted input.** Text from web pages, emails or documents can carry
  persistent injections. Require approval before untrusted content becomes procedural
  memory (`agent-guardrails`).
- **Users can see and delete** their memories; same PII retention as traces
  (`agent-observability`).
- **Eval cases:** a fact needed from an earlier session, a stale fact that must be ignored,
  no leakage across users.

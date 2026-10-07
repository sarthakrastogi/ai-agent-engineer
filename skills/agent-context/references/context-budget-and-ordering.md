# Context budget and ordering

## Layout

Order from most stable to most volatile: this serves the cache and puts the freshest,
task-relevant tokens at the end, where attention is strong.

| # | Block | Stability | Notes |
|---|---|---|---|
| 1 | Tool definitions | Fixed for the run | Changing them invalidates the whole cache; mask instead (`prompt-caching.md`). |
| 2 | System prompt | Fixed per version | No timestamps, user names or request IDs. |
| 3 | Stable reference context | Fixed per session | Glossary, schema summaries, user profile. Keep small. |
| 4 | Retrieved memories / long docs | Per session or task | Before the question. |
| 5 | History: messages, tool calls, results | Append-only | Cleared or compacted as it grows (`memory-and-compaction.md`). |
| 6 | State recitation | Rewritten each step | `todo.md`: goal, done, next. |
| 7 | Current user turn | Per turn | Question last. Dynamic data (current time) goes here. |

- **Most relevant chunks at the edges**; the middle of the window is used worst.
- **Own the serialisation.** Dense typed event records ("tool X → status, 3 key fields,
  pointer") beat raw message dumps. Serialise deterministically: sorted keys, fixed formats.
- **Mid-run guidance is a new message**, never an edit to the system prompt or earlier
  turns.

## Always-on vs on-demand

Context assembly is a curation step before every model call, not a prompt written once.

- **Always-on (invariants):** rules every call needs — standards, glossary, project facts.
  Keep it small; it is paid every turn.
- **On-demand (playbooks):** procedures some requests need. Give each a name and a one-line
  description; load only on match (a cheap model or keyword rules can match).
- **Conflicting always-on layers: the more specific wins** (project over workspace). Say so
  in the prompt so the model doesn't reconcile them itself.

### Two-stage selection for large corpora

1. Build a lightweight index: paths, exports or titles, one-line summaries.
2. A cheap model picks the relevant subset under a hard cap (`max_files`).
3. Read only the selected items in full for the main model.

If everything looks relevant, the request is too broad: split or clarify it first.
Irrelevant context degrades quality non-linearly. Ranking retrieved chunks is `agent-rag`.

## Budgeting

There are no universal percentages; set budgets from your profile.

1. **Baseline** each block (system, tools, stable context, history, tool results,
   retrieved) at median and p95 turn.
2. **Window ceiling** well below the model limit, from your quality-vs-length curve.
   Distraction commonly appears past ~100K tokens, far earlier on weaker models.
3. **Per-block cap with an action** on hit: clear tool results, compact history, cap
   retrieval top-k, defer tools behind search.
4. **Cap tool outputs at the source** with pagination and truncation guidance (~25K tokens
   max per result; `agent-tools`).
5. **Re-check after every change**; budgets drift as tools and prompts grow.

## How contexts fail

| Failure | In traces | Fix |
|---|---|---|
| **Poisoning** | A wrong "fact" is re-cited in later turns, plans or summaries. | Purge it from summaries and goals; verify facts with tools before they enter state. |
| **Distraction** | Repeats earlier actions, ignores new information, leans on history. | Clear or compact history; recite the plan at the end. |
| **Confusion** | Wrong or irrelevant tool chosen; superfluous context used. | Fewer tools, tool search, masking per state; remove irrelevant context. |
| **Clash** | Contradictory instructions or facts across turns or sources. Instructions sharded across turns lose substantial accuracy. | Consolidate instructions up front; drop superseded facts on compaction. |
| **Lost instructions** | Early rules (format, constraints) stop being followed late. | Recite key rules near the end; restate format every 3–5 turns; enforce in code. |
| **Drift by imitation** | Repetitive history few-shots the agent into the same action pattern. | Vary serialisation and phrasing of observations. |

## Measuring

Capture per LLM call (OTel GenAI names; OpenInference uses `llm.token_count.*`):

```text
turn_record = {
  trace_id, turn_index, model,
  input_tokens:        gen_ai.usage.input_tokens          # includes cached
  cache_read_tokens:   gen_ai.usage.cache_read.input_tokens
  cache_write_tokens:  gen_ai.usage.cache_write.input_tokens
  output_tokens:       gen_ai.usage.output_tokens
  reasoning_tokens:    gen_ai.usage.reasoning.output_tokens
  compacted:           gen_ai.conversation.compacted
  by_block: {system, tools, history, tool_results, retrieved}   # your own count
}
```

Per-block counts aren't in standard telemetry: count them where you assemble context
(provider token-count endpoint or tokenizer) and log them as span attributes.

| Signal | Use |
|---|---|
| Input tokens by turn index | Steep growth usually means tool results. |
| Block share | High tool-result share → clearing pays off. |
| Cache hit rate | Definitions per source in `prompt-caching.md` → Monitoring. |
| Quality vs peak input tokens | Bucket eval or online-judge outcomes; the drop point is your ceiling. |
| Tokens and turns per successful task | Efficiency metric reported beside success rate. |
| Ablation | Re-run the eval with one block removed or shrunk; if the score holds, it was noise. |

# Prompt caching

Agents re-send a growing prefix every turn and input dwarfs output (~100:1), so cache hit
rate is the main cost and latency lever. Cached reads cost ~0.1x input and cut time to
first token.

## Rules

1. **Byte-stable prefix.** Tools, system prompt and stable context first, unchanged
   mid-run. One changed byte invalidates everything after it.
2. **No timestamps, request IDs or per-user values at the top.** Put the time in the latest
   user turn.
3. **Append-only history.** Edit, reorder or re-summarise earlier turns only at a deliberate
   compaction point, accepted as a cache reset.
4. **Deterministic serialisation:** sorted JSON keys, fixed whitespace and number formats.
5. **Mask tools, don't remove them.** Keep the full list stable and restrict per state.
   Editing the list invalidates the cache and confuses the model when earlier turns
   reference a missing tool.
6. **Clear and compact in large steps** so each cache reset buys real headroom.
7. **Pass thinking blocks back unmodified** (Claude); add guidance as new messages, not
   `system` edits.

Typical Claude breakpoints: end of tools + system, end of stable context, last message
(moved forward each turn).

## Tool masking

| Approach | How |
|---|---|
| Provider allow-list | OpenAI: stable `tools`, `allowed_tools` per request. |
| Constrained decoding | Mask logits so only allowed tool names can be produced. Shared prefixes (`browser_`, `shell_`) make group masking easy. |
| Prompt-level state | Say in the latest turn which tool group applies, backed by a code check that rejects disallowed calls. Weaker but portable. |
| Anthropic mid-conversation tool changes | Leave `tools` as first sent; append `role: "system"` messages with `tool_addition` / `tool_removal`. See provider specifics below. |

## Provider specifics

Verify against current provider docs.

**Anthropic**
- Opt-in: up to 4 `cache_control` breakpoints, 20-block lookback each.
- Cache order `tools → system → messages`. Changing tools invalidates everything; changing
  `tool_choice` or images invalidates messages. Thinking/effort changes invalidate messages
  or more, depending on model.
- Minimum cacheable length 512–4,096 tokens by model; below it caching silently doesn't
  happen. Confirm via `cache_creation_input_tokens`.
- Reads 0.1x base input (0.05x Opus 5.5, 0.025x Fable 5.1); writes 1.25x (5-min TTL) or 2x
  (1-hour TTL).
- Pre-warm with a `max_tokens: 0` request before a traffic burst. Batch (−50%) stacks with
  caching; use the 1-hour TTL for batches.
- Mid-conversation tool changes (beta): declare tools up front with `defer_loading: true`
  and toggle by reference, or define inline (header `inline-tools-2026-09-15`; by-reference
  changes also under `mid-conversation-tool-changes-2026-07-01` on Claude API, Bedrock,
  Vertex). Keep at least one non-deferred tool in `tools`, or the first inline definition
  is a full cache miss. Keep those system messages in later requests.

**OpenAI**
- Automatic for prompts ≥ 1,024 tokens; reads ~0.1x. No breakpoints, so ordering does all
  the work.
- `prompt_cache_key` routes related requests to one cache (~15 req/min per key on older
  models).
- Monitor `usage.prompt_tokens_details.cached_tokens`; restrict tools with `allowed_tools`.

**Others / self-hosted** (e.g. vLLM prefix caching): same prefix-match rules; check
minimums, TTLs and pricing.

## Monitoring

Hit rate = cached input ÷ total input, per call. Denominators differ:

| Source | Formula |
|---|---|
| OTel | `gen_ai.usage.cache_read.input_tokens / gen_ai.usage.input_tokens` (input includes cached) |
| OpenAI raw | `cached_tokens / prompt_tokens` (prompt includes cached) |
| Anthropic raw | `cache_read_input_tokens / (input_tokens + cache_creation_input_tokens + cache_read_input_tokens)` |

- **Chart per turn index.** Healthy agents climb high after turn 1 and stay there. Dips
  aligned with deploys, compaction or specific tools locate the mutation.
- **Alert on a sustained drop** after a release.
- **Find the breaker** by diffing the serialised prefix of two consecutive turns; the first
  differing byte is the culprit.

## Common cache breakers

| Breaker | Fix |
|---|---|
| `Current date: …` in the system prompt | Move it to the latest user turn. |
| Tools added or removed per state | Stable list plus masking, or a cache-preserving tool-change mechanism. |
| Unordered JSON in tool results or context | Sorted keys, fixed serialiser. |
| RAG block inserted before history | Append retrieved content after history or in the current turn. |
| Per-user greeting or profile at the top | Move it after stable blocks or into a cached per-user segment. |
| Editing an earlier message to fix it | Append a correction. |

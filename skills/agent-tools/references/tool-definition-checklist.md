# Tool definition checklist

## 1. The tool set

Start from the tasks in `design.md`, then design the fewest tools that cover them. An API's
endpoint list is input, not the answer.

| Signal | Action |
|---|---|
| Calls always made in sequence (`find_user` → `get_orders(user_id)`) | Merge into one task tool (`get_customer_context`) |
| Tools that dump many records for the agent to search (`read_logs`) | A search/filter tool (`search_logs(query, since)`) |
| Several CRUD tools on one resource, similar parameters | One tool with an `action` enum |
| Modes that share almost no parameters | Split; models fill sparse schemas badly |
| Two tools a human would hesitate between | Merge, remove one, or add "use the other when…" to both |
| A tool the agent never needs on the eval set | Remove it |

**Tools the set usually lacks:**

- **Live-state reads for whatever the agent writes to** (current schema, config, policies,
  logs), so writes target real state.
- **Verification tools, fast and slow:** a fast deterministic check (tests, schema, lint) on
  every iteration, and a slow high-fidelity one (real browser, end-to-end run) used
  selectively. Return failures the agent can act on.

**Counts:**

- Tool search / deferred loading at 10+ tools or > ~10K tokens of definitions; skip it under
  10. It cuts definition tokens sharply and improves selection accuracy.
- ≤ ~20 tools loaded at once. Around 30+ overlapping tools, selection degrades badly; small
  models fail earlier. Overlap matters more than count.
- Don't edit the set mid-run; mask instead (`agent-context` → `references/prompt-caching.md`).

## 2. Names and namespaces

- Verb + object, snake_case, specific: `search_tickets`, `create_refund`; not `tickets`,
  `do_action`.
- Namespace by service when tools come from several sources (`github_list_prs`,
  `jira_search_issues`). Prefix vs suffix behaves differently per model; choose by eval.
- Consistent prefixes (`browser_`, `db_`) let you mask or allow tool groups.
- Unambiguous parameters: `user_id`, `start_date`, `max_results`; not `user`, `date`, `n`.

## 3. Parameter schemas

- Type every parameter: `enum` for closed sets, `format`/pattern for dates and IDs,
  `minimum`/`maximum`, `required`.
- One `status` enum, not three booleans that can contradict. Test: could a new intern call it
  correctly from the definition alone?
- Require absolute paths if relative ones cause errors; accept natural formats (ISO dates,
  names) over formats that need counting (line offsets, diff headers).
- **Never make the model fill what code knows:** tenant, user identity, auth tokens, current
  time, the record in focus. Inject them in the handler; this also closes a spoofing route.
- Flat schemas; nest only when structure is the point.
- Turn on strict tool use / structured outputs. Where a model rejects forced `tool_choice`,
  use `auto` with strict tools.
- A rationale parameter asks for "a short explanation", not step-by-step reasoning.
- Pass tools via the API `tools` field, never pasted into the prompt.

## 4. Descriptions

Write for a new teammate who knows nothing about your system. At least 3–4 sentences:

```text
<What it does, in one sentence, with the resource it acts on.>
Use when <situations>. Do not use for <near-miss situations>; use <other_tool> instead.
<Parameters: meaning, format, defaults, interactions; query syntax if any.>
<Returns: fields, count, ordering, pagination. What it does NOT return.>
<Caveats: side effects, rate limits, latency, permissions, data freshness.>
```

- Spell out jargon, query syntax and how resources relate ("a project contains boards; pass
  `project_id` from `search_projects`").
- "Use this tool when…", not "CRITICAL: You MUST…"; newer models over-trigger on shouting.
- Cross-tool policy ("look up the order before refunding") goes in the system prompt
  (`agent-prompting`), not in each description.

## 5. Examples in definitions

- For nested or format-sensitive inputs add 1–3 example calls (`input_examples` where
  supported, else an "Example:" line). This substantially improves complex-parameter accuracy.
- ~20–200 tokens each. Realistic, varied values; show optional fields in at least one. Skip
  for simple tools.

## 6. Read vs write tools

Apply the risk-tier controls in `agent-guardrails` → `references/approvals-and-permissions.md`
(low: bounded, logged; medium: preview, idempotency key, return what changed, code limits,
audit; high: blocking approval on exact arguments).

- Reads and writes in separate tools, so reads are allowed freely and writes gated.
- `dry_run` / preview on writes; the high-risk approval UI shows its output.
- Authorise in the handler with the end user's identity and scoped credentials.
- Rate-limit and log every write. Agent reads untrusted content → `agent-guardrails` before
  shipping any write tool.
- Secrets come from env or a secret manager in the executor from the first prototype, never
  inline.
- Query-building tools bind model-supplied values as parameters; never format them into SQL.

## 7. Testing tools with the agent

1. Write 30+ realistic multi-step tasks with real data shapes, plus a held-out set you don't
   tune on.
2. Record per task: success, tool calls, wrong-tool choices, invalid-argument errors, tokens,
   wall-clock.
3. Classify failures in transcripts: invalid tool, invalid parameters, wrong values, goal
   failure, inefficiency.
4. Fix the least powerful thing first: description → schema → response shape → merge/split.
5. Give the agent the failing transcripts and definitions and have it rewrite the
   descriptions.
6. Re-run both sets; keep changes that improve the held-out set. Log in `experiment-log.md`.

## 8. Review checklist

- [ ] Each tool maps to a task; no endpoint-for-endpoint wrapping.
- [ ] No two tools a human would hesitate between.
- [ ] 10+ tools or > ~10K tokens → tool search considered; ≤ ~20 loaded.
- [ ] Names verb_object, namespaced across services.
- [ ] Every parameter typed; enums for closed sets; required marked; no ambiguous names.
- [ ] No parameter the code already knows (identity, tenant, auth, time).
- [ ] Description ≥ 3–4 sentences: what, when, when not, parameters, returns, caveats.
- [ ] Examples for complex inputs.
- [ ] Results bounded; pagination/truncation with guidance.
- [ ] Errors actionable with a correct example; no empty success on failure.
- [ ] Writes idempotent, scoped, logged; high-risk writes need approval; authz in code.
- [ ] Definitions stable within a session.
- [ ] Tested on realistic tasks with a held-out set; results logged.

# Model migration

## What changes between models

- **API surface:** parameters removed or redefined.
- **Behaviour:** verbosity, tool-call eagerness, parallel calls, delegation, refusal style,
  instruction literalness.
- **Prompt fit:** emphasis written for a weaker model ("CRITICAL: you MUST…") makes newer
  models over-trigger.
- **Tokeniser and pricing:** same prompt, different token count; cost per task and cache
  minimums change.
- **Harness fit:** models are trained with specific harnesses; tool shapes, edit formats and
  compaction that suited the old model may not suit the new one. Keep safety guarantees
  (permissions, approvals, caps) in code so they survive unchanged.
- **Provider state:** thinking blocks, cache entries, response IDs don't carry across models
  or providers.

Verify against current provider docs. Recent Claude examples: last-turn prefill removed,
forced `tool_choice` rejected on some models, `budget_tokens` replaced by effort,
`max_tokens` includes thinking.

## Triggers

Retirement date, a promised cost/quality gain, a provider change, or a nightly drift-run
regression with no change on your side (release-pipeline.md). Start well before retirement:
eval, shadow and canary take time.

## Process

1. **Baseline** the current version on the full eval set: quality, cost per successful task,
   p50/p95, tool calls per task, cache hit rate. Save the run.
2. **Read the target's migration guide**; list removed/changed parameters, new defaults,
   known behaviour changes.
3. **Swap the model ID on a branch** and fix API breaks: prefill → structured output; forced
   `tool_choice` → `auto` with strict tools; `budget_tokens` → effort; re-size `max_tokens`
   to include thinking; handle a `refusal` stop reason with a fallback.
4. **Pass provider state back unchanged**; expect any router or fallback to another model
   to drop it.
5. **Fresh effort sweep.** Don't carry settings over.
6. **Re-tune prompts:** strip old-model emphasis and over-prompting, add back only what
   evals show is needed. Re-check tool descriptions, few-shot examples, tool granularity,
   edit format, compaction.
7. **Eval gate:** iterate on ~20 real cases, then the full suite with paired comparison vs
   baseline, plus the attack set. Judge agent end state, not each step.
8. **Re-baseline cost and latency**; update budgets and alert thresholds.
9. **Shadow, then canary** (versioning-and-rollouts.md). Watch online judges, escalation,
   refusal rate, cost per task.
10. **Log** in `experiment-log.md` (eval deltas, effort, prompt diffs, cost/latency,
    decision); update model and retirement date in `design.md`.

## Ship rule

Ship when the regression suite holds, the paired capability difference is non-negative (or
a measured drop is explicitly accepted by the user for a cost/latency gain), the attack set
passes, and cost and latency are within budget. Otherwise stay and record why.

## Cross-provider extras

- Re-map structured-output and tool-calling features; strict-schema support differs.
- Re-check prompt layout conventions for long contexts (instruction placement differs by
  model family).
- Re-validate LLM judges if the judge model changes.
- Re-check data-handling terms, regions and retention with the user.

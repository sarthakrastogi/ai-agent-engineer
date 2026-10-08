# CI gates and online evals

## Eval-driven development

Write the eval with the change: objective (criterion or mode) → cases that exhibit it →
grader → paired comparison with repeats → cases join regression. Back-test every prompt
change against a library of past production queries, not only the targeted cases; fixes
for one edge case often break another.

Cadence: assertions on every change; model and human evals on a schedule; A/B tests after
major changes. Each layer catches holes in the others.

## Every run records

- Per eval: pass rate with 95% CI, n, pass^k where relevant.
- Cost (tokens in/out/cached, $) and latency (p50/p95 per case, wall time).
- Git SHA, model ID and settings, prompt, dataset, judge prompt and judge model versions.
- Per-case JSONL, so runs diff case by case and failures open as traces.

A +2 points that doubles p95 is a trade-off for the user, not a win.

## Noise

95% CI half-width `±1.96·√(p(1−p)/n)`, in points:

| n cases | p = 0.5 | p = 0.8 | p = 0.9 |
|---|---|---|---|
| 20 | ±22 | ±18 | ±13 |
| 50 | ±14 | ±11 | ±8 |
| 100 | ±10 | ±8 | ±6 |
| 200 | ±7 | ±6 | ±4 |
| 400 | ±5 | ±4 | ±3 |

Use Wilson intervals for small n or p near 0/1. Compare versions with paired differences
(`quick-paths.md`, *Comparing two versions*); clustered cases need clustered SEs; average k
trials per case. Use a power analysis when the decision matters. Reproduction run counts:
`agent-accuracy` → `experiment-discipline.md`.

## CI tiers

| When | What runs | Gate |
|---|---|---|
| Every commit | Offline checks, no keys: routing on fixed inputs, prompt files present, token-budget estimates. Seconds | Blocks |
| PR touching prompts, tools, model config, agent code | Code checks + regression set (often 100+), 1–3 trials | Blocks |
| Nightly / pre-release | Full suite with judges, k trials, cost/latency | Blocks release |
| Nightly vs production | Full suite on the deployed system | Alerts; no repo change + new failures = drift |
| On demand | Capability set | Information |

Gate rules:

- **Block** when the regression suite falls below its absolute threshold, **or** the
  paired difference vs `main` has its CI below −margin (smallest regression the user
  cares about).
- Reliability-critical flows gate on **pass^k (k ≥ 3)**.
- **Gate cost and latency** vs a committed baseline: default block at +20% latency or +30%
  cost. Update the baseline only by a deliberate manual run.
- Never gate on capability evals.
- **No retry-until-green.** Run flaky cases k times and gate on the rate; quarantine and
  track, don't delete.

Thresholds: start from measured baseline minus noise. Tie to business cost where possible
(break-even accuracy from cost of a failure vs value of a success). Typical factual-error
tolerance: ~5–10% internal tools, ~2–3% high-risk. Write thresholds and reasons down
(`eval-plan.md` → `Gates` if used).

Practicalities:

- Cache agent outputs and verdicts keyed by (input, version, judge version).
- Forked PRs can't read secrets; run the gate on a trusted branch.
- Post a per-metric table (current, baseline, delta, threshold) as a PR comment.
- Feed every fixed production failure into the regression set.
- Pipeline stages and deploys: `agent-production` → `release-pipeline.md`.

## Run cost

```text
cost per run ≈ cases × k × (agent cost per case + judges × judge cost per verdict)
e.g. 200 × 3 × ($0.04 + 4 × $0.005) ≈ $36; nightly ≈ $1,100/month
```

- Judges only where code can't decide; run only the evals a PR can affect.
- Batch API (~−50%) for non-blocking nightly runs; retire judges that always pass.
- Separate API key or workspace for evals so runs can't eat production rate limits.
- Record the budget (`eval-plan.md` if used); print the estimate with every run.

## Online evals

- **Triage, not a gate:** async judges score after the answer has shipped. Anything that
  must stop a bad answer runs synchronously in the response path (`agent-guardrails`).
- Only reference-free evaluators: code checks, validated judges, user and outcome signals.
- Sample judging separately from tracing: e.g. 10% of traces plus all with negative
  feedback, a given tool, or a high-value tier.
- Backfill ~100 historical traces first to check the judge reads the right fields and span.
- Report bias-corrected rates with CIs (`judge-validation.md`); alert on relative change;
  confirm alerts by reading traces.
- Flagged traces feed the next error-analysis round.
- Agree with the user what content may be judged and stored.
- User and outcome signals: `agent-observability` → `metrics-dashboards-alerts.md`.

## Linking scores to traces

Attach every score to the span it judged, as OTel GenAI event `gen_ai.evaluation.result`:

```python
span.add_event("gen_ai.evaluation.result", attributes={
    "gen_ai.evaluation.name": "refund_amount_correct",
    "gen_ai.evaluation.score.label": "fail",
    "gen_ai.evaluation.score.value": 0.0,
    "gen_ai.evaluation.explanation": "Quoted a 60-day window; policy chunk says 30.",
    "gen_ai.response.id": response_id,
})
```

- Async/offline judges: the span has ended; emit a log record with its trace and span IDs,
  or use the backend's score API. OpenInference backends use `evaluation.*` /
  `annotation.*`.
- Name scores for what they measure (`refusal`, not `refusal judge`); check target filters
  so traces aren't scored twice.
- Score the observation holding the content; OTel trace-level I/O may be empty.

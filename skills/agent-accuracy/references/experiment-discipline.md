# Experiment discipline

## Before changing anything

1. **Set up the comparison** per `agent-evals` → `references/quick-paths.md` (*Comparing two
   versions*): pinned versions, frozen environment, ≥ 3-run baseline as the noise floor.
2. **Write the hypothesis** in the log entry: mode, why the change helps, expected
   direction and size.

One change per experiment. If changes must ship together, measure them separately first.

## Runs to reproduce a failure

P(≥ 1 failure in k runs) at true failure rate q, `1 − (1 − q)^k`:

| q \ k | 3 | 5 | 10 | 20 | 30 |
|---|---|---|---|---|---|
| 50% | 0.88 | 0.97 | 1.00 | 1.00 | 1.00 |
| 20% | 0.49 | 0.67 | 0.89 | 0.99 | 1.00 |
| 10% | 0.27 | 0.41 | 0.65 | 0.88 | 0.96 |
| 5% | 0.14 | 0.23 | 0.40 | 0.64 | 0.79 |

- **Reproduce:** k ≈ 3 / q (≈ 5 at 50%, ≈ 15 at 20%, ≈ 30 at 10%); 20–30 when unknown.
- **Confirm a fix (rule of three):** 0 failures in n runs bounds the rate below ~3/n. 10
  clean runs still allow ~30%; proving "under 10%" takes ~30 clean runs.

## Deciding

- **Keep:** the quick-paths verdict is "better" on the target mode with no other mode below
  −margin, and cost and latency are within budget. Confirm once on test, then add
  reproduced failures to the regression set.
- **Revert:** target didn't move beyond noise, or a regression appeared elsewhere.
- **Iterate:** target moved but a regression appeared; localise the regression before
  stacking another change.

## Overfitting to the eval

- Test cases read to design a fix become dev; replenish test from new traffic.
- Never put eval cases in prompts, few-shots or fine-tuning data.
- Write fixes as principles, not the failing case's specifics. Design on half the failing
  category, check on the other half.
- Prompt optimisers refine against known failures but can't find new ones; use only on
  solid, representative evals.
- Synthetic-only sets overfit to the generator; confirm on real queries.
- Tuned against an LLM judge? Spot-check 25–50 outputs with the expert (judges favour
  length and their own style).
- Saturated evals give no signal; add harder cases.
- Prefer the signal closest to the product goal over proxies.
- Re-run error analysis periodically; fixes shift the failure distribution.

## Log entry

Log every experiment, failed ones included (in `agent-engineering/experiment-log.md` if the
project uses it):

```markdown
## 2026-10-06 — Refund amount from order record
- Change: prompt v13 → v14, one rule: "take the amount from get_order, never from the user"
- Hypothesis: wrong_amount (18% of fails) comes from trusting user-stated amounts
- Eval: `make eval-refunds`, dataset refunds@v4 (dev, n=120, k=3), judge wrong_amount v2
- Result: wrong_amount 18% → 6% (paired Δ −12 pts, CI [−17, −7]); regressions: none outside noise
- Cost/latency impact: +40 input tokens/call; p95 unchanged
- Decision: keep; test split confirmed 5%; 9 cases added to regression set
```

## When to stop

Stop and tell the user which applies:

- The agreed target (`eval-plan.md` if used) met with the CI's lower bound above it, or
  business break-even reached.
- Last 2–3 experiments within noise at this rung, and the next rung costs more than the
  remaining failures are worth.
- Remaining failures need a product decision; list them.
- Remaining failures are below what the set can resolve; needs a bigger dataset or
  production A/B.

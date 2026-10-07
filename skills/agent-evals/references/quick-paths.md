# Quick paths

## Comparing two versions

Use when an eval set exists and the question is "is B better than A?" (prompt edit, model
upgrade, new tool).

1. **Same everything except the change:** dataset version, split (dev while iterating),
   judge prompt and model, fixtures, pinned settings.
2. **Know the noise floor.** Run the baseline ≥ 3 times; the spread is the smallest change
   you can claim. CI half-widths: `ci-and-online-evals.md`.
3. **k = 3–5 trials per case** for stochastic agents, averaged per case before
   differencing. Repeats remove within-case noise; only more cases remove between-case
   noise.
4. **Paired difference with a CI** on the same cases, not two independent rates. On 100
   cases near 80%, differences under ~8 points are noise.
5. **Clustered cases** (same document, conversation, template) can make the true SE > 3×
   the naive one; analyse per cluster.
6. **Per failure mode and tag:** a +3 overall can hide −10 on one mode. List every
   previously passing regression case that now fails, by ID.
7. **Cost and latency** for both versions: tokens, $ per successful task, p50/p95.
8. **Verdict:** better if the CI of the difference is above zero (or above the user's
   margin) and no mode's CI is below −margin. Otherwise report "no detectable
   difference"; don't round it to a win.

```python
import math, statistics as st
def paired_diff(base, cand):
    """base, cand: {case_id: [1/0 per trial]} on the SAME cases → mean diff, 95% CI."""
    ids = sorted(base.keys() & cand.keys())
    d = [st.mean(cand[i]) - st.mean(base[i]) for i in ids]
    mean, half = st.mean(d), 1.96 * st.stdev(d) / math.sqrt(len(d))
    return mean, (mean - half, mean + half)
```

Taste comparisons with no reference: pairwise judge in both orders
(`graders-and-judges.md`). To fix what regressed: `agent-accuracy`.

## Minimal eval

Use for **one objective failure** checkable in code: invented order IDs, broken JSON,
wrong tool for a known intent, missing required field.

1. **20–50 cases from real failures**, plus a few that should pass so an over-correcting
   fix shows up. Provenance and dataset version.
2. **One code check** decides pass/fail: schema validation, cited IDs ⊂ retrieved IDs,
   expected tool name, end state. No judge, so no judge validation.
3. **Baseline with k = 3**; save per-case results with SHA and versions; fix; compare
   paired (above).
4. Add the cases to the regression set once the fix lands.

Graduate to the full workflow when the failure needs a judge, there are several failures
and you don't know which matters, the check passes but users still complain, or the eval
will gate releases.

## Auditing an existing suite

- [ ] **Mapping:** each eval maps to a success criterion or failure mode. Orphan generic
      metrics go.
- [ ] **Provenance:** where cases came from, when, and whether the mix still matches
      traffic. Synthetic expected outputs are a red flag.
- [ ] **Leakage:** no eval cases in prompts, few-shots or fine-tuning data; test split not
      used for iteration; judge few-shots not from dev/test.
- [ ] **Judges validated:** TPR and TNR on held-out expert labels (> 0.9 target, 0.8
      floor), re-checked since the last judge or model change. Unvalidated judges are
      information, not gates.
- [ ] **Noise and k:** run-to-run spread known; stochastic agents run k ≥ 3; set big
      enough for the deltas people act on.
- [ ] **Thresholds justified:** written down, set from baseline minus noise or business
      cost, not a round number.
- [ ] **Saturation and breakage:** evals at ~100% (move to regression) and tasks at 0%
      over many trials (broken task or grader).
- [ ] **Cost to run** per run and per month; a suite too expensive to run gets skipped.
- [ ] **Read 10–20 failing transcripts** and confirm verdicts with the domain expert.

Record keep / fix / drop per eval in `eval-plan.md`. Gaps in mapping or judge validation
send those evals back through the full workflow.

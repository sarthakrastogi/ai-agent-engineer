# Judge validation

Required before gating on, reporting or acting on any LLM-judge result.

## Convention

**PASS is the positive class.** State it (in `eval-plan.md` if used); some tools use the
opposite.

- **TPR** = judge PASS when expert PASS = TP / (TP + FN).
- **TNR** = judge FAIL when expert FAIL = TN / (TN + FP).

Never report raw agreement when failures are rare: at 5% failures, always-PASS is 95%
"accurate" with TNR = 0. The same applies to guards and classifiers: ask for TPR and FPR
and compute precision at your own base rate (at a ~1% attack rate, a 5% FPR flags ~5
benign users per real attack).

## 1. Labels

- **Minimum ~100 expert-labelled traces, ~50/50 pass/fail;** oversample rare failures.
  That gives only ~20–25 per class in dev and in test; usable, wide intervals.
- **150–200 for tight intervals** (30–50 per class per split). At TNR 0.90 the 95% CI
  half-width is ~±0.17 with 12 FAIL labels, ±0.11 with 30, ±0.08 with 50.
- Labellers see the judge's fields plus the full trace, are blind to the judge's verdict,
  and write a one-line reason.
- Non-expert labellers: short tutorial plus a comprehension check on pre-labelled cases.
- Several labellers: double-label a shared batch, compute Cohen's κ. Low human agreement →
  fix the criterion definition before touching the judge.

## 2. Split

| Split | Share | Use |
|---|---|---|
| train | 10–20% | Source of judge few-shot examples |
| dev | 40–45% | Iterate the judge; never copied into the prompt |
| test | 40–45% | Run once at the end to report TPR/TNR |

## 3. Iterate on dev

1. Run the judge on dev; list false passes and false fails.
2. Read each disagreement; decide if the judge or the label is wrong. Fix wrong labels with
   the expert and log it.
3. Change one thing: sharper definition, better borderline example (from train),
   less/different context, stronger model.
4. Repeat; expect 2–4 iterations to reach 0.9.

## 4. Test once

- **Target TPR and TNR > 0.90; floor 0.80.** Below the floor, the judge only triages traces
  for humans; no gates, no reported numbers.
- Weigh by cost: missed failures expensive → prioritise TNR; false alarms blocking
  releases → prioritise TPR. Record the choice.
- Iterating after seeing test spends it; label fresh test cases before reporting again.
- Exclude UNKNOWN from TPR/TNR; report the UNKNOWN rate.
- Record n, TPR, TNR, date, judge prompt version and model (`eval-plan.md` if used).

## 5. Correct the pass rate (Rogan-Gladen)

```text
θ̂ = (p_obs + TNR − 1) / (TPR + TNR − 1)      clip to [0, 1]
```

Example: TPR 0.95, TNR 0.70, observed 80% → θ̂ = 0.50 / 0.65 ≈ 0.77. A lenient judge
overstates quality. If `TPR + TNR − 1` is near 0 the judge is near chance; don't correct,
don't use.

## 6. Bootstrap CI

Resample both the labelled test split and the production sample, 2,000 iterations, report
2.5th–97.5th percentiles (`judgy` implements this):

```python
import random
def theta(h, j, p):                       # h, j: expert / judge bools on test (True=PASS)
    pos = sum(h); neg = len(h) - pos      # p: judge bools on production traces
    if pos == 0 or neg == 0: return None
    tpr = sum(a and b for a, b in zip(h, j)) / pos
    tnr = sum((not a) and (not b) for a, b in zip(h, j)) / neg
    d = tpr + tnr - 1
    return None if d <= 0 else min(1, max(0, (sum(p) / len(p) + tnr - 1) / d))

def bootstrap_ci(h, j, p, iters=2000):
    pairs, out = list(zip(h, j)), []
    for _ in range(iters):
        hs, js = zip(*random.choices(pairs, k=len(pairs)))
        t = theta(hs, js, random.choices(p, k=len(p)))
        if t is not None: out.append(t)
    out.sort()
    return out[int(0.025 * len(out))], out[int(0.975 * len(out))]
```

Report `θ̂ [low, high]`, not the raw judge rate.

## Re-validate when

- the judge prompt, model or provider changes;
- the agent's model or prompt changes enough that outputs look different;
- the product policy behind the criterion changes;
- spot checks (25–50 traces per error-analysis round) disagree with the expert more than
  the test TPR/TNR predicts.

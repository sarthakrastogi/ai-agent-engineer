# Graders and judges

Validation is in `judge-validation.md`.

## Pick the cheapest grader that works

| Grader | Use for | Weakness |
|---|---|---|
| **Code**: exact match, regex, schema, unit tests, SQL executes, state checks | Format, required fields, tool + args, cited IDs ⊂ retrieved IDs, end state, budgets | Brittle to valid variation |
| **LLM judge** | Tone, faithfulness, relevance, policy adherence, "asked the clarifying question" | Non-deterministic, costs money, must be validated |
| **Human expert** | Judge labels, spot checks, new failure discovery, high-stakes launches | Slow, expensive |

- Many "subjective" checks have an objective core (a refund answer must contain the
  amount). Split hybrids: code for that part, a judge for the rest.
- Test code graders on known passes and fails; a regex that never fires reads as 100%.
- A fine-tuned classifier (e.g. NLI for factuality) suits low-latency online guards; it
  generalises poorly outside its domain.

## Binary verdicts

Gate on binary pass/fail with a written critique. 1–5 scales have undefined gaps, drift to
the middle, and can't be validated with TPR/TNR. Express severity as several binary judges
(`wrong_amount`, `rude_tone`). A judge may also emit a score for diagnosis only.

**Pairwise** ("which of A/B is better on X?") is more stable than absolute scoring for
taste. Use it to compare versions, both orders, and keep the absolute gate so you don't
ship the less bad of two failing versions.

## Writing a judge prompt

One judge per failure mode, with four parts:

1. One criterion, from the failure taxonomy.
2. Pass and fail definitions in observable terms.
3. ≥ 3 examples: clear pass, clear fail, **borderline**, each with a detailed critique
   (terse critiques are an anti-pattern). From the **train split only**.
4. Structured output, critique before verdict.

Also:

- Pass only the fields the criterion needs (chunks + answer for faithfulness, not the whole
  trace). Ablate context choices during validation.
- Offer `UNKNOWN`; count it separately. A rising rate means missing trace data.
- Name the property precisely: faithfulness ≠ completeness. For multi-part questions add a
  completeness judge that checks each sub-question was answered.
- Temperature 0 where allowed; parse with a schema; parse failures are their own count,
  never pass.
- Judge prompts are versioned files; record the version with every result.

```text
You evaluate ONE criterion: <criterion name, from failure-taxonomy.md>.

PASS if: <observable definition>.
FAIL if: <observable definition, including the common borderline failure>.
If the input does not contain enough information to decide, answer UNKNOWN.

<examples>
<example verdict="PASS"> <input>…</input> <critique>detailed reasoning…</critique> </example>
<example verdict="FAIL"> … </example>
<example verdict="FAIL" note="borderline"> … </example>
</examples>

<input>
{only the fields this criterion needs, e.g. <context>…</context> <answer>…</answer>}
</input>

Return JSON: {"critique": "<reasoning that cites the input>", "verdict": "PASS|FAIL|UNKNOWN"}
```

## Judge model

- Start with the most capable model in budget; downgrade only if the cheaper one keeps
  TPR/TNR on test.
- Same family as the agent is acceptable if it meets TPR/TNR on held-out test. Prefer a
  different family for pairwise and open-ended quality judgements (self-preference).
- The judge prompt is always separate and criterion-specific; never let the system grade
  itself with its own prompt.

## Biases

| Bias | Mitigation |
|---|---|
| Position (order flips pairwise verdicts in 50–70% of cases) | Run both orders; win only if consistent, else tie |
| Verbosity (longer preferred > 90%) | Criterion-specific definitions; length-matched borderline examples |
| Self-preference | Different family for pairwise; validate |
| Expertise gap (judges agree with non-experts more than experts) | Validate against domain-expert labels |

## Upkeep

- Retire expensive judges that pass consistently; replace with a cheap check or periodic
  sample.
- Re-validate after changing the judge prompt, judge model, agent model or product policy.

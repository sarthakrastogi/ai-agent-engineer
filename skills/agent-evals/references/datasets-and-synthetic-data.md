# Datasets and synthetic data

## Sizes

| Purpose | Size |
|---|---|
| First agent eval suite | 20–50 tasks from real failures |
| Early iteration, large effects (30% → 80%) | ~20 real queries |
| Error discovery | ~100 diverse traces |
| Judge validation | ~100 expert-labelled, ~50/50 pass/fail; 150–200 for tight CIs; < ~60 too wide |
| CI regression set | small, purpose-built, often 100+ |
| Human review batch | 25–50 |

Start small; grow from new failures. Prefer more cases with slightly noisier automated
grading over a few hand-graded ones.

## Sources of cases, in order

1. Production traces: error-analysis failures, negative feedback, escalations, incidents.
   Stratify by intent, segment, outcome.
2. Adjacent logs: support tickets, search logs, the manual process being replaced, the bug
   tracker, manual pre-release checks.
3. Expert-written edge cases and policy boundaries.
4. Synthetic inputs along dimensions, to fill gaps.

With 100+ real traces, stratify-sample and skip synthetic. Synthetic-only sets overfit to
the generator; confirm on real queries.

## Case schema

One JSON object per line in `agent-engineering/datasets/<name>.jsonl`:

```json
{"id": "refund-017",
 "input": {"messages": [{"role": "user", "content": "..."}]},
 "context": {"account_tier": "pro", "fixtures": "orders_v3"},
 "expected": {"outcome": "refund_created", "amount": 42.00, "max_latency_s": 15, "max_tokens": 6000},
 "reference": "Optional reference answer or rubric notes",
 "tags": ["refund", "edge:partial", "persona:frustrated"],
 "split": "dev",
 "provenance": {"source": "prod", "trace_id": "t_0151", "added": "2026-10-01", "by": "jo"}}
```

- `expected` holds what code can check: end state, tool called, route chosen, required
  steps run, budgets. Assert properties, not exact output strings.
- `reference` only where a judge needs it.
- `tags` include the targeted failure mode(s), so rates can be sliced.
- `provenance` is mandatory. Redact secrets and personal data first.

## Good cases

- **Unambiguous:** two domain experts would reach the same verdict independently.
  Otherwise fix the task.
- **Balanced:** cases where the behaviour should happen and where it shouldn't (refuse /
  don't refuse; call tool / answer directly). For classifiers (guard, router), balance
  classes, add hard negatives (benign inputs with trigger words; `agent-guardrails` →
  `input-output-guards.md`), and report TPR/FPR, not accuracy.
- **Edge cases:** irrelevant, missing, overlong or harmful input; ambiguity; facts deep in
  context; multi-turn dependencies.
- **Counterfactual pairs for bias:** swap gender, group or name terms; grade the pair for a
  material difference in outcome, tone or refusal.
- **Pinned fixtures** (DB snapshot, mock tool responses, file tree) per case.
- **A task at 0% across many trials is usually broken** (wrong reference, impossible spec,
  grader bug). Read transcripts first.

## Synthetic generation

1. Pick ~3 dimensions: intent/feature, persona/context, query property (difficulty,
   ambiguity, length, language). Target a difficulty mix of ~30% easy / 50% medium / 20%
   hard; easy-heavy sets saturate.
2. Hand-write ~20 tuples (`refund × first-time user × ambiguous amount`); the domain
   expert checks realism and coverage.
3. LLM generates more tuples; dedupe; drop impossible combinations.
4. Turn tuples into messages **in a separate call** (joint generation repeats phrasing).
5. Filter by hand: keep inputs rated ≥ 4/5 for realism; aim for ~100.
6. Check each input actually triggers its condition; run the agent and read traces.

```text
Generate 1 realistic user message for this scenario. Vary vocabulary and length;
write as a real <persona> would, including typos if natural. Do not solve the task.
Scenario: feature=<f>; persona=<p>; property=<q>
Return only the message.
```

- **Generate inputs only, never expected outputs.** Write references by hand or derive
  them from fixtures.
- High-stakes domains (legal, medical, financial) and low-resource languages: an expert
  reviews every synthetic case.
- Multi-turn: LLM-simulated user with persona and goal, or N-1 testing (real prefix + next
  turn).
- Retrieval: questions per chunk plus adversarial queries using vocabulary from similar
  non-answering chunks (`agent-rag`).

## Splits, versions, upkeep

- Agent datasets: `dev` to iterate, held-out `test` to confirm. Test cases read to design a
  fix move to dev; replenish test from new traffic.
- Judge-label sets use train/dev/test (`judge-validation.md`).
- Never copy dev/test cases into prompts or few-shots.
- Version datasets (`refunds@v4`, content hash or git tag) and record the version in every
  result and log entry.
- Separate **regression** (near 100%, gates) from **capability** (hard, starts low). Move
  saturated capability cases into regression.
- Every fixed production failure becomes a regression case. Refresh when a set saturates;
  re-sample after major traffic or product changes.

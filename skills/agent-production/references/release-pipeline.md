# Release pipeline (CI/CD for agents)

Test behaviour, not just code: a provider model change, a one-line prompt edit or a routing
bug passes unit tests. Gate statistics: `agent-evals` → `references/ci-and-online-evals.md`.
Rollout stages: versioning-and-rollouts.md.

## Stages

| # | Stage | Trigger | Runs | Blocks? |
|---|---|---|---|---|
| 0 | Local | Before a PR | Offline checks + live suite against a local app | — |
| 1 | Offline checks | Every commit | No keys or services: routing logic on fixed inputs, prompt files load, token-budget estimate per case vs context window. Seconds | Yes |
| 2 | Live eval gate | PRs touching prompts, tools, model config, retrieval, agent code | Real app with real dependencies (CI service containers), health-checked, golden dataset end to end, agent not mocked. Minutes | Yes |
| 3 | Baseline comparison | After 2 | Quality, latency, tokens, cost per case vs baseline | Yes |
| 4 | Trace verification | After 2 | Path assertions from traces | Yes |
| 5 | Attack regression set | Prompts, model, tools or guards change | `attacks.jsonl` (`agent-guardrails`); any success blocks | Yes |
| 6 | Build + deploy | Merge | Image tagged with git SHA as `service.version`; release unit recorded | — |
| 7 | Post-deploy smoke | After deploy | Suite subset against the deployed env | Rollback |
| 8 | Rollout | After 7 | Canary, ramp, online evals | Rollback triggers |
| 9 | Nightly drift run | Daily | Full suite against production | Alerts |

- Give developers two commands (e.g. `make evals-offline`, `make evals`); both pass before a
  PR.
- The app's own runtime checks (grounding, completeness) count as gates only once validated
  as judges (`agent-evals`).
- Forked PRs can't read API keys; run stage 2 on a trusted branch.

## Golden dataset

- Assert properties, not exact outputs: expected route/model, sub-question count, faithful,
  complete, latency bound (e.g. ≤ 15 s for complex), token budget. Format: `agent-evals` →
  `references/datasets-and-synthetic-data.md`.
- Cover every route (simple → small model, complex → large, multi-part → fan-out) so a
  routing bug fails a specific case.
- ~8 cases proves the pipeline, not the agent; grow to 50–100+ from feedback, production
  failures and adversarial sessions.

## Baseline comparison

- Keep a baseline file in the repo (per case: pass/fail, scores; per run: p50/p95, tokens,
  cost per task), or run `main` and the PR head to head on the same cases (paired, no
  staleness, 2× cost).
- Block on: a previously passing case now failing; a significantly negative paired quality
  difference; latency or cost regression over threshold (start at 20% latency, 30% cost;
  tune).
- Update the baseline only deliberately (manual workflow with an `update_baseline` input),
  never automatically on green.
- Tokens from provider usage fields, not string-length estimates.
- Post regressions as a PR comment, one line each:

```text
BLOCKED: Eval regressions detected
  - case icloud-cancel-photos: previously passing case now fails
  - completeness: current 0.4, below threshold 0.6
```

## Trace verification

A right answer by the wrong path (simple question routed to the large model) passes quality
checks at ~10× the tokens. Assert from traces:

- route and model match the case's expectation;
- each validation step ran and produced a real score, not a default;
- decomposed questions fanned out and every sub-answer reached the response;
- no forbidden tool called; side-effecting tools ran at most once.

Requires route/model attributes on spans (`agent-observability`).

## Testing the agent's code

| Layer | Checks | How |
|---|---|---|
| Unit, mocked LLM | Loop control, routing, parsers, reducers, caps, error handling, executor policy | Fake client returning scripted responses: tool call, malformed JSON, refusal, 429, `length` stop |
| Tool contract | Schema, error shape, side effects match what the model is told | Validate example calls against the schema; assert actionable errors and idempotency (same key → one effect) |
| Record / replay | Orchestration on real model output, deterministically | Cassettes keyed by request hash; re-record on model or prompt change, never hand-edit; scrub secrets and PII |
| Integration | App with real dependencies | Service containers; one run per route |
| Evals | Behaviour and quality | Stages 2–4 |

Mocked-LLM tests never replace the eval gate. Every code bug gets a unit test; every
behaviour failure gets an eval case.

## Nightly drift run

- Nothing changed in repo, config or data and evals fail → the model or provider changed.
  Pinned snapshots reduce but don't remove this (retrieval data, tools, serving change).
- Respond with a logged change: pin a snapshot if on an alias, tighten the prompt, or move
  affected query types to another model via model-migration.md. Never lower the threshold
  to pass; thresholds are product decisions in `eval-plan.md`.
- Run on a test tenant or with side-effecting tools stubbed.

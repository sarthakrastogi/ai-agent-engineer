# <Agent name> — launch checklist

Go through this with the user before the first real traffic. Each line names the skill
that covers it. An unchecked box is a launch decision to make on purpose, not a blocker
by default. Record each "no" and who accepted it in `design.md` → Risks.

## Quality
- [ ] Success criteria in `design.md` each have an eval with a threshold (`agent-evals`)
- [ ] The eval suite was run on the release candidate; results logged with versions
- [ ] Every LLM judge used as a gate is validated (TPR/TNR on a held-out split)
- [ ] Reliability measured where it matters: pass^k on the critical tasks, not one run
- [ ] Regression cases from past failures are in the suite (`agent-accuracy`)

## Safety
- [ ] Trifecta check done per context window; mitigations in place (`agent-guardrails`)
- [ ] Write/money/external-message tools have their risk tier and control
- [ ] Attack regression set passes on this release (`datasets/attacks.jsonl`)
- [ ] Secrets come from env/secret manager; none in prompts, code or traces
- [ ] Residual risk accepted by a named person

## Observability
- [ ] A test run produces the expected span tree with tokens, cost and errors
      (`agent-observability` → instrumentation health)
- [ ] PII decision made: what's captured, redacted, retained, and for how long
- [ ] Dashboards: success rate, p95 latency, cost per task, tool error rate
- [ ] Alerts fire (tested), with an owner
- [ ] Online evals sample production; user feedback is captured and linked to traces

## Production
- [ ] Bounds: max turns, timeouts, token/cost cap per task (`agent-production`)
- [ ] Retries are bounded; side-effecting tools are idempotent
- [ ] Model and prompt versions pinned and recorded on every trace
- [ ] Provider quotas and rate limits checked against expected peak traffic
- [ ] Fallback per dependency decided (model, retrieval, tools): degrade, hand off, or fail
- [ ] Rollout plan (shadow → canary → full) with a rollback trigger and a kill switch
- [ ] Handoff to a human exists for out-of-scope requests and repeated failures
- [ ] Incident runbook: how to find a bad trace, disable a tool, roll back a prompt

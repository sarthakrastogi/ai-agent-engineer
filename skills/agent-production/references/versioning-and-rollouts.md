# Versioning and rollouts

## The release unit

A change to any of these is a new agent version:

```yaml
# agent-release.yaml — one per deployable version
agent_version: 2026.10.06-3
model: <provider snapshot id>        # pinned, never an alias
params: {effort: medium, max_tokens: 8000, temperature: null}
prompts: {system: sha256:9b1e…, planner: sha256:41ac…}
tools: {schema_sha: 3f2c…, impl: tools-lib@1.8.2}
mcp_servers: {crm: crm-mcp@0.4.1}
retrieval: {index: kb-2026-10-01, embedder: <id>, reranker: <id>}
guardrails: {config_sha: 77d0…}
framework: <agent-framework>@<version>
eval_run: <link to the gating eval run>
```

- Record model (`gen_ai.request.model`), agent version and prompt versions on every trace,
  or regressions can't be attributed (`agent-observability`).
- Prompts and tool descriptions live in version control, reviewed like code. Git plus a
  content hash is enough; add a registry only if non-engineers edit prompts, and keep it
  versioned and eval-gated.
- A tool-description wording change is a behaviour change: run evals.
- Tag the image with the git SHA and use it as `service.version`.

## Pinning models

- Snapshot IDs in production, never floating aliases. Check each provider's naming.
- Track deprecation and retirement dates in `design.md`; start migration well before.
- Pin embedder and reranker too; changing the embedder means re-indexing.

## Pre-release gate

1. Regression suite (near 100%) and capability evals on the candidate.
2. Paired differences on the same items vs production, with 95% CI; clustered SEs when
   items share a source.
3. Reliability-critical stochastic tasks: k runs, gate on pass^k.
4. Attack regression set (`agent-guardrails`); any success blocks.
5. Cost per task and p95 within budget.

Block on any failure. Statistics: `agent-evals`. CI wiring: release-pipeline.md.

## Rollout stages

| Stage | What runs | Exit |
|---|---|---|
| Offline eval | Candidate on eval sets | Gate passes |
| Shadow | Copy of live traffic; output discarded | Online judges, cost, latency comparable to control |
| Canary | 1–5% of real traffic | No rollback trigger over the window |
| Ramp / A/B | Larger split with control | Online evals and outcomes ≥ control |
| Full | 100% | Previous version stays deployable |

Size splits and windows by volume so the canary sees enough tasks to detect the effect that
matters (power analysis: `agent-evals`).

**Shadow:** stub or block every side-effecting tool. Read-only tools may run for real if
load allows; otherwise replay recorded results. Use the same judges and checks as
production.

**Online evals:** sample both arms (e.g. 10% plus all negative-feedback traces) with the
same validated judges. Prefer outcome signals (task completed, draft accepted, escalation,
regenerate rate) over opinion signals. Alert on change relative to control; read traces
before acting.

**Long-running agents:** run old and new side by side; route new runs to the new version
gradually; let in-flight runs finish on their starting version (changed code can break
checkpoint replay).

## Rollback

- Write triggers before rollout (design.md Production section): regression pass rate,
  online-judge delta vs control, error and escalation rates, p95, cost per task, high-risk
  tool anomalies.
- Rollback is a config flip to the previous release unit; test it beforehand.
- Add the failing traces to the eval set before retrying.

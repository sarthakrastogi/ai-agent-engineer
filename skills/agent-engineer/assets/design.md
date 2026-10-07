# <Agent name> — design

## Problem
<!-- fill: who uses it, what job it does for them, what happens today without it -->

## Success criteria
<!-- fill: testable statements. Each needs a metric + threshold + how it's measured.
e.g. "≥ 90% of support tickets in the eval set get the correct routing label (code check)"
e.g. "p95 end-to-end latency ≤ 8 s", "cost ≤ $0.05 per task" -->

| Criterion | Metric | Threshold | Measured by |
|---|---|---|---|
|  |  |  |  |

## Scope
- In scope:
- Out of scope (agent must refuse or hand off):

## Architecture
<!-- fill: single call | workflow (which pattern) | single agent | multi-agent — and WHY the
simpler options were rejected -->

- Pattern:
- Models (and why):
- Knowledge sources / retrieval:
- State & memory:
- Human-in-the-loop points:

```
<diagram of the flow>
```

### Tools
<!-- risk tier per agent-guardrails: low (read-only) / medium (reversible writes) / high
(irreversible, money, external messages) -->

| Tool | Purpose | Read/write | Risk tier | Control (none / preview / approval / limits) |
|---|---|---|---|---|

## Context strategy
<!-- fill: what goes in the system prompt, what's retrieved just-in-time, what's summarised,
how long runs are compacted -->

## Risks & guardrails
Trifecta: private data <yes/no> · untrusted content <yes/no> · exfiltration path <yes/no>
<!-- all three yes → architectural mitigation required, see agent-guardrails -->

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Prompt injection via <source> |  |  |  |

Residual risk accepted by: <!-- fill: name, date -->

## Production
<!-- fill via agent-production: reliability (timeouts, retries, idempotency, durable state),
cost & latency budgets and how they're enforced, pinned model + prompt versions, rollout
plan (shadow / canary / A-B) and rollback trigger, on-call / incident notes -->

## Open questions
-

## Decision log
| Date | Decision | Alternatives considered | Reason |
|---|---|---|---|

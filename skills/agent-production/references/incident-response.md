# Incident response for agents

## Incident types

| Type | Signal | First containment |
|---|---|---|
| Harmful or wrong action | Destructive call, wrong refund, wrong recipient | Disable the tool; approve-all mode; pause affected runs |
| Data leak / injection exploit | Canary hit, unexpected sink call, user report | Disable the exfil channel; revoke credentials; preserve traces (`agent-guardrails`) |
| Runaway cost or loops | Spend, token or turns-per-run spike | Lower caps; kill runs over cap; check for injected or looping inputs |
| Silent quality regression | Online-judge drop, escalation or regenerate rate up, nightly eval fails | Roll back the release unit |
| Provider outage | 429/5xx, latency spike | Evaluated fallback model, degraded mode, queue and resume |
| Tool or dependency failure | Error rate by tool | Circuit-break; return a clear limitation |
| Harmful content | Moderation flags, reports | Tighten output guard; roll back prompt change |

## Build before launch

- Kill switches that need no deploy: per-tool disable, per-tenant disable, approve-all
  (every high/medium-risk call needs a human), global pause of new and in-flight runs.
  Each flippable in seconds.
- Rollback as a config flip (versioning-and-rollouts.md).
- Credential revocation path per tool and MCP server.
- Traces retained long enough to investigate, versions on every span, content per the PII
  policy (`agent-observability`).
- Alerts on rollback triggers and the signals above, routed to a named owner, linking a
  runbook that lists the switches and who may pull them.

## Runbook

1. **Declare.** Name a lead; note time and triggering alert or report.
2. **Contain before diagnosing.** Pull the narrowest switch that stops the harm (tool disable
   before global pause; approve-all before shutdown). Security incidents: revoke
   credentials first.
3. **Scope** via traces by agent version, tool, time window: runs, users, tenants, side
   effects. Durable-execution logs and the idempotency ledger show which actions executed.
4. **Remediate side effects.** Reverse what can be reversed. Ask the user about notification
   and disclosure obligations; don't assume.
5. **Roll back** for quality regressions; fix forward only through the eval gate.
6. **Resume** paused runs only after purging injected content from their state or memory.

## After the incident

- Triggering traces become eval cases: regressions into the regression suite
  (`agent-evals`), attacks into `attacks.jsonl` (`agent-guardrails`).
- Add the failure mode to `failure-taxonomy.md`; fix and eval delta to `experiment-log.md`.
- Ask what would have caught it earlier (cap, alert, eval case, approval placement); fix the
  control, not just the prompt.
- Blameless write-up: timeline, impact, causes, actions with owners.

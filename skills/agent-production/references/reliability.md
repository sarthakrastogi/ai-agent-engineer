# Reliability

## Classify the failure first

| Failure | Examples | Response |
|---|---|---|
| Provider transient | 429, 500/502/503, overloaded, reset, stalled stream | Backoff + jitter, honour `retry-after`; then fallback or fail |
| Provider permanent | 400, removed parameter, context too long, auth, spend-cap 429 (no `retry-after`) | Don't retry. Fix config, compact, or fail loudly |
| Tool transient | Downstream timeout, 5xx, lock contention | Retry in the tool layer if idempotent; else surface |
| Tool semantic | Bad args, not found, permission denied | Actionable error to the model; counts toward consecutive errors |
| Tool silent failure | `null`, `[]` or truncated body with no error | Normalise to an explicit error in the wrapper; flag the span (`agent-observability`). Otherwise the model answers confidently from nothing |
| Model behaviour | Malformed output, schema violation, refusal, repeated identical call | Validate in code; one corrective re-ask; then escalate |
| Process | Crash, deploy, OOM, preemption | Resume from last checkpoint |
| Run-level | Turn, time, token or spend cap hit | Stop, save state, return partial result or hand off |

Tell the model what failed and why, but keep deterministic safeguards around it.

## Timeouts

- **LLM call:** connection timeout plus a stream *idle* timeout (no tokens for N s), not
  just a total.
- **Tool:** 2–3× the tool's observed p99; tighten with data.
- **Run:** wall-clock and turn limits from the latency budget and the longest passing eval
  trajectory.
- Return timeouts as actionable errors ("search timed out after 20 s; narrow with
  `since=`"), not stack traces.

## Retries

- Exponential backoff with full jitter: `sleep = random(0, min(cap, base * 2**attempt))`.
- 3–5 attempts for provider calls, plus a retry budget per run.
- **One retry layer.** SDKs already retry (typically 2); frameworks add more; 3 × 3 × 3 =
  27 attempts per logical call in an outage. Pick one layer, set the others to 0.
- Retry only idempotent or idempotency-keyed operations.

## Idempotency for side-effecting tools

20k runs/day × 6 tool calls × 0.5% failures × 3 retries ≈ 1,800 chances a day to double a
refund or email. Durable execution still replays a call that succeeded just before the
checkpoint was written.

```text
def send_email(args, ctx):
    key = f"{ctx.run_id}:{ctx.step_id}"          # stable across replays and retries
    if (prior := ledger.get(key)) is not None:
        return prior
    result = mail_api.send(**args, idempotency_key=key)
    ledger.put(key, result)
    return result
```

- Derive the key from run + step identity, never a random value at call time.
- Prefer downstream APIs that accept idempotency keys; otherwise a ledger with a unique
  constraint.
- Compare parameters on a reused key and error on mismatch, so changed arguments on retry
  don't get a stale "success".
- No natural dedupe (posting a message): record intent before, result after; on replay,
  check the destination before acting.

## Durable execution

Use when runs exceed a request timeout, wait on humans or webhooks, or have expensive
steps. Skip for short single-shot requests.

- Checkpoint each LLM and tool call; replay from the last success; retry per step, not per
  run.
- Human waits persist state and use no compute; resume on signal or webhook.
- Options: workflow engine (Temporal, Inngest, Restate, DBOS, step functions), framework
  checkpointer, or your own event log in a DB.
- Replay-based engines need deterministic workflow code: put LLM calls, tools, clocks and
  randomness in activities/steps.

## Own state and control flow

- Agent as stateless reducer: `next_step = llm(serialised_state)`; your code executes tools
  and appends results to an event log you own.
- Unify execution state with business state so resume, audit and support read one record.
- Expose launch, pause, resume, cancel. Pausing is how approvals, compaction and incident
  response work.
- Only deserialise state you wrote.

## Loop and runaway guards

- Max turns and tool calls per run. Exits: final output, no tool call, error, or cap.
- Same tool + same args N times in a row → stop and escalate.
- Token and spend cap per run and per user/tenant per day.
- Limit input at the edge before guards, retrieval or the model: reject oversized or
  malformed requests. Rate-limit per authenticated user, not per IP.
- **Consecutive-error counter** (canonical threshold; other skills point here): increment on
  each tool or validation error, reset on success, stop and escalate at ~3.
- Test the caps fire: eval cases like "repeat this word 100,000 times" or "for each of these
  1,000 items, analyse and give three alternatives" must stop cleanly on output, turn and
  spend caps (`agent-guardrails` → `references/red-teaming.md`).

**Unattended or scheduled runs** need the loop essentials (`agent-design` →
`references/the-agent-stack.md`): observable goal, termination condition, escalation of hard
blockers, the caps above. Ask who receives escalations when nobody is watching. Default to
one task at a time from a visible queue the user can pause, reorder and edit.

## Fallbacks and degraded modes

- **Fallback per dependency is a business decision.** Propose fail open, degrade or fail
  closed per dependency, state it and let the user correct it; write the table into
  `design.md` if used. The LLM provider down is
  always a clean, explicit failure. Never fail open in front of high-risk tools. Put the
  fallback in calling code, not inside the breaker.
- Default when retrieval or a tool is down: answer with a stated limitation or hand off, not
  a guess.
- **Circuit breaker** per failing dependency (e.g. open after 5 consecutive failures,
  half-open probe after 30 s) so runs fail fast instead of each burning timeout × retries.
- **Fallback model** is a release: eval it. Provider state (e.g. thinking blocks) is dropped
  on fallback.
- Run heavy local models (guard classifiers, embedders, PII pipelines) as separate services
  with their own memory limit and a health endpoint the breaker probes.

## Provider capacity and quotas

- **Size demand before launch:** peak runs/min × LLM calls/run × tokens/call, input and
  output separately, per model. Input tokens/min usually binds first. Check whether cached
  reads count toward the limit (on most Claude models they don't).
- Per-minute limits may be enforced per second, and sharp jumps hit acceleration limits:
  ramp launch traffic.
- **Load-test the agent, not the endpoint:** replay a realistic eval-task mix at 1×, 2× and
  peak concurrency, side effects stubbed or on a test tenant. Measure p95, 429 rate,
  retries/run, cost, pass rate. Include long runs; they hold concurrency longest.
- **Shape load:** queue with per-tenant concurrency, interactive ahead of background,
  offline on batch, a clear "busy, try again" over retry cascades.
- Alert at 70–80% of quota at peak (from rate-limit headers). Request increases weeks ahead.
- **Multi-provider fallback, cheapest risk first:** same model on another platform (check
  caching, tool features, output limits), then a different model (a release: eval it, keep
  its prompt variant, record on the trace, alert on failover). Fail over on an open breaker,
  not a single error.

## Escalation to a human

Make it a tool: `escalate(reason, summary, state_ref)` called by the agent or by the
executor on a threshold; the run pauses until a person resumes or closes it. Escalate on
the consecutive-error threshold, caps hit, high-risk actions (`agent-guardrails`),
low-confidence output on high-stakes tasks, explicit user request.

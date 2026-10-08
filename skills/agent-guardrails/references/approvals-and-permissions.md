# Approvals and permissions

## Rate every tool

Score write access, reversibility, blast radius and financial impact; the highest wins.
This is the pack's canonical tier table; `agent-design` and `agent-tools` point here.

| Tier | Examples | Required controls | Human placement |
|---|---|---|---|
| Low | Read own data, search, get, list, dry-run, reversible edits in a sandbox | Bounded output; rate limit; log | None |
| Medium | Write the user's own records, draft (not send), reversible tickets, capped reversible money movement | Preview/dry-run where the effect isn't obvious; idempotency key; return what changed; code caps and rate limits; audit log; anomaly alerts | Sample-review the audit log; no blocking approval |
| High | Send externally, pay/refund over cap or irreversibly, delete, deploy, change permissions/config, write shared systems, act visibly as the user | Medium controls + exact-argument preview, hard cap in code, scoped credentials — or remove the tool | Blocking approval; pause, persist, resume |
| Any | Repeated failure or out-of-scope request | Stop the loop (threshold: `agent-production` → `references/reliability.md`) | Escalate to a human as a tool call |

**Money movement** is Medium only with all of: per-transaction and per-user-per-period caps
in code, an idempotency key, a reversal path, an audit log, and alerts on anomalies (spikes
per user, amounts clustering just under the cap). Over the cap or irreversible (wires,
crypto, gift cards): High. Cap values are a business decision: propose them
and let the user set them.

Then per tool:

- **Functionality:** needed at all? Remove it if evals don't drop.
- **Permissions:** can it do more than the task needs? A reporting agent's `run_sql` that
  can `DROP` needs a read-only role or a parameterised query tool.
- **Autonomy:** does a high-impact call happen with no check?

## Enforce authorization in code

```text
async def execute(call, session):
    tool = REGISTRY[call.name]
    args = tool.schema.validate(call.args)               # reject malformed input
    args["tenant_id"] = session.tenant_id                # never from the model
    if not authz.allowed(session.user, tool.name, args): # same check a UI action hits
        return tool_error("Not permitted for this user.")
    if (err := enforce_limits(tool, args, session)):     # caps, rate limits, spend: every tier
        return tool_error(err)
    if tool.risk == "high":
        decision = await approval(call, args, session)   # blocks; bound to hash(args)
        if not decision.approved:                        # rejected or timed out
            return tool_rejected(decision.reason)        # tell the model; don't execute
    return tool.run(args, creds=session.scoped_creds(tool.name))
```

- Limits run before approval, so an approved call still can't exceed caps. An approver's
  edit is a new call: run it through `execute()` again.
- Fill identity, tenant and ownership from the session; never make the model fill
  arguments code already knows.
- Reuse the authz path a human hits via UI/API; no second, weaker one for the agent.
- Hard caps in code (refund ≤ $200, ≤ 10 recipients, ≤ 100 rows deleted), not in the prompt.
- Rate-limit per user and per tool, cap spend per run, log every call.

## Credentials

- **Run in the user's auth context** (delegated OAuth, on-behalf-of) so the agent can't
  exceed the user. Service identity only for actions no user owns, narrowly scoped.
- Short-lived, scoped per tool, separate read and write, no wildcards.
- **Never in the context.** Inject in the executor; assume prompt and context leak.
- **No token passthrough.** An MCP server accepts only tokens issued for it and doesn't
  forward the user's upstream token.

## Sandboxing

Executing generated code, shell or untrusted packages needs both:

- **Filesystem isolation** — else it escapes the workspace or reads on-disk credentials.
- **Network isolation** — else keys, env vars and data leave. Egress via a proxy with a
  domain allowlist.

Also: no secrets in the sandbox env, CPU/memory/time limits, ephemeral per run, monitor
what runs. A good sandbox also cuts permission prompts sharply. Unattended runs: exact tool
allowlist, deny everything else; pilot on 2–3 items before the full batch.

A browser verifier using the **user's logged-in session** can do anything the user can:
rate it High unless the session is scoped to a preview/test environment, run it in a
remote sandbox, and never follow links or instructions from pages outside the app under test.

## Human-in-the-loop

### What to gate

Gate: irreversible actions; sends to new/external recipients; over-cap or irreversible
money; permission, config or credential changes; deletes; shared-system writes; first use
of a capability in a session; any post-untrusted-content action a policy flags; repeated
failure.

Don't gate: reads, reversible local edits, and Medium actions bounded by code caps. Each
unnecessary prompt trains users to click through.

### Mechanics

1. **Pause** at the tool call and **persist** run state (durable execution,
   `agent-production`); waiting costs no compute.
2. **Show the exact action:** tool, every argument, and each argument's *source* —
   highlight values from untrusted content (a recipient taken from an email body).
3. **Approve, edit or reject.** Bind approval to a hash of the arguments; any change
   re-approves.
4. **Execute exactly what was approved**, then resume.
5. **Timeout = deny.** Log approver, decision, latency.
6. High stakes: the approver isn't the person whose request triggered it.

Only deserialise run state you wrote; resumed state is an injection path.

### Approval fatigue

Users approve the vast majority of permission prompts without reading. Cut prompts with
allowlists, sandboxes and code caps; approve plans instead of calls where plan-then-execute
fits. A gate approved nearly every time without edits is unnecessary or rubber-stamped —
investigate.

**Classifier-gated auto-approval** for Medium calls: a fast gate approves safe calls,
blocks risky ones with a reason so the agent can try another way, and falls back to a human
after repeated blocks.

- The gate sees only the user's task and the pending action — never tool outputs or the
  agent's reasoning — so injected content can't argue past it.
- It reduces prompts; it isn't the boundary. High-tier keeps blocking approval and caps.
- Trace every gate decision; a sensitive action with no gate span is P0
  (`agent-observability` → `references/metrics-dashboards-alerts.md`).

## MCP server trust

Before connecting a server:

- **Provenance:** maintainer, official or community, source available? Treat it as a
  third-party dependency.
- **Pin** version or hash; re-review tool descriptions on every update (servers can change
  them after approval).
- **Read tool descriptions as untrusted text** — they enter context and can carry
  instructions or shadow other servers' tools.
- **Scope credentials** minimally; progressive scopes; no wildcards.
- **Run local servers sandboxed;** show the full launch command before first run.
- **Remote servers you build:** no token passthrough, per-client consent in OAuth proxies,
  exact `redirect_uri` match, single-use `state`, random session IDs never used for auth,
  SSRF blocks on private ranges and `169.254.169.254`.
- **Re-run the trifecta check** — a new server can add the missing leg.

Audit third-party skills the same way: someone else's instructions and code.

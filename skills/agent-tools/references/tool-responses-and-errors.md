# Tool responses and errors

## Response shaping

- Return the fields the next decision needs, not the raw payload. Drop internal metadata,
  nulls, audit fields and unused nested blobs.
- Human-readable values (`name`, `status: "overdue"`) over UUIDs, status codes and epoch
  times. Include an ID only when a later call needs it, and make it short or semantic
  (`ticket-4821`); opaque UUIDs get hallucinated.
- Formats close to natural text (JSON, Markdown, plain lines); choose by eval and stay
  consistent across tools.
- Offer `response_format` (`concise` default, `detailed` on request) when some callers need
  IDs and metadata for follow-ups. Concise is often a third of the tokens.

### Pagination, filtering, truncation

- Every list/search tool takes filters (`since`, `status`, `owner`), a small default limit and
  a cursor; returns the total count. Filter server-side.
- When truncating, say so and say how to narrow:

```text
Showing 25 of 1,342 results (newest first).
Narrow with since="2025-03-01", project="billing", or status="open"; next page: cursor="c_25".
```

- Cap every tool's output, usually well under 25K tokens. One oversized result degrades every
  later step (`agent-context`).
- File and document reads support ranges (offset/limit, pages, sections) and return the size.

### Large artefacts and bulk work

- Write large outputs to storage; return a reference (path, URL, ID) plus a short summary.
- When the agent must join, aggregate or transform many results, let it do so in code (code
  execution, or programmatic tool calls from a script) and return only the result. This can
  cut tokens by an order of magnitude or more. Keep a tool model-facing only when the model
  must see each intermediate.
- Where a well-known CLI exists (`gh`, `aws`, `kubectl`) and the agent has a sandboxed shell,
  it is often the most context-efficient interface.

### Sensitive data

Return handles for PII and secrets and resolve them in code at the point of use. Tool output
from the outside world is untrusted input and can carry prompt injection (`agent-guardrails`).

## Errors

State what was wrong, the expected form, and a correct example. Never a stack trace or bare
status code.

```text
Error: start_date must be ISO-8601 (e.g. "2025-03-14"); got "next Tuesday".
Error: no customer with email "jon@acme.co". Did you mean "john@acme.co"? Search with
       search_customers(query=...) if unsure.
Error: refund amount 1,200.00 exceeds the order total 120.00 for order ord-5521.
```

Instead of `ValueError: invalid literal for Decimal: '£45'`, return:

```text
Error: amount must be a number in the order's currency without symbols (e.g. 45.00); got "£45".
Order ord-5521 is in GBP; maximum refundable is 120.00.
```

Return errors as a tool result flagged `is_error: true` so the loop continues and the model
sees it; don't raise an exception that kills the run.

| Class | Message should contain | Retry? |
|---|---|---|
| Invalid arguments | Field, expected format, correct example | Model fixes and retries |
| Not found | What was searched, nearest matches, which tool finds valid IDs | Model searches, retries |
| Ambiguous match | Candidates with distinguishing fields | Model picks or asks the user |
| Permission denied | That the user lacks permission, not how to bypass it | No; tell the user or escalate |
| Rate limit / quota | When to retry | Code retries with backoff; model told only if it persists |
| Timeout / upstream failure | Transient; whether the write may have happened | Code retries idempotently, then tells the model |
| Business rule violation | The rule and the values that broke it | Model adjusts or escalates |

- **Never return `null`, an empty list or an empty body for a failure.** After retries,
  return an explicit error with its class and `retryable`. Empty-looking success on a rate
  limit produces confident wrong answers ("you're covered") that unit tests miss. Reserve an
  empty result for a search that truly found nothing, and say so
  (`{"results": [], "note": "no orders since 2026-09-01"}`).
- Retry transient failures (timeouts, 429, 5xx) with bounded backoff in code before the model
  sees them. Set a timeout on every call and report it as an actionable error.
- Writes take idempotency keys so a retry after timeout can't apply twice; the error says
  whether the write may have taken effect.

### Triage and escalation

- **Recoverable** (bad syntax, malformed field, a not-found the agent can search around) →
  back to the model.
- **Hard blockers** (missing credentials or permission, a case policy doesn't define, a
  required human input) → stop and escalate at once without spending retry budget. Mark
  `retryable: false` so code, not the model, decides.
- Count consecutive tool errors and escalate past a threshold (`agent-production` →
  `references/reliability.md`).
- Keep failed attempts in context so the agent doesn't repeat them; compact them away once
  resolved (`agent-context`).

### Diagnosing tool failures

| Failure in traces | Usual fix |
|---|---|
| Invalid tool chosen | Description, names, overlap |
| Invalid parameters | Schema, enums |
| Wrong parameter values | Examples, description of formats |
| Goal failure (tools worked, task not done) | Task design, missing tool |
| Inefficiency (too many calls) | Response shape, merge tools |

Track counts per class (`failure-taxonomy.md` if used).

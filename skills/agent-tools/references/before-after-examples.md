# Before / after tool rewrites

Adapt names and fields to the user's domain. Definitions use a provider-neutral JSON shape.

## 1. Endpoint wrappers → one task tool

**Before:** three tools mirroring REST endpoints; the agent must chain them and often skips
the availability check.

```text
list_users()            → all users (10,000 rows)
list_events(user_id)    → all events for a user
create_event(user_ids, start, end, title)
```

**After:**

```json
{
  "name": "calendar_schedule_meeting",
  "description": "Schedules a meeting at the first time all attendees are free. Use when the user asks to book, set up or find time for a meeting. Do not use to move or cancel an existing meeting; use calendar_update_meeting. Attendees are matched by email; unknown emails return an error listing close matches. Searches working hours (09:00-17:00 in each attendee's time zone) within the window given. Returns the booked slot and event_id; does not send an agenda.",
  "input_schema": {
    "type": "object",
    "properties": {
      "attendee_emails": {"type": "array", "items": {"type": "string", "format": "email"}, "minItems": 1},
      "duration_minutes": {"type": "integer", "enum": [15, 30, 45, 60, 90]},
      "earliest": {"type": "string", "format": "date", "description": "ISO-8601 date, inclusive"},
      "latest":   {"type": "string", "format": "date", "description": "ISO-8601 date, inclusive"},
      "title":    {"type": "string", "maxLength": 120}
    },
    "required": ["attendee_emails", "duration_minutes", "earliest", "latest", "title"]
  },
  "input_examples": [{"attendee_emails": ["ana@acme.co", "raj@acme.co"], "duration_minutes": 30,
                      "earliest": "2025-03-17", "latest": "2025-03-21", "title": "Q2 planning"}]
}
```

Changed: task-level tool, namespaced name, when / when-not, enum instead of a free integer,
explicit formats, stated return value, an example. The organiser comes from the session, not
a parameter.

## 2. Raw response → shaped response

**Before:** API payload passed through (~1,900 tokens for 10 results).

```json
{"data":[{"id":"9f1c2a7e-4b1d-4c3e-8a2f-0d6b1e9c7a55","type":"ticket","attributes":{"subj":"Login loop","st":3,"cust_ref":"c0a8...","created":1710403200,"sla":null,"tags":[],"custom_fields":{...}}}, ...],"meta":{"page":{"cursor":"eyJvZmZ..."}}}
```

**After:** concise by default, readable values, explicit truncation.

```text
10 of 214 open tickets matching "login loop" (newest first):
- tkt-4821 | Login loop after password reset | open | Acme Ltd | 2025-03-14
- tkt-4790 | Stuck on SSO redirect | open | Globex | 2025-03-12
...
More: cursor="c_10". Narrow with since= or customer=. Use response_format="detailed" for IDs and SLA fields.
```

## 3. Traceback → actionable error

**Before:**

```text
Traceback (most recent call last):
  File "handlers.py", line 88, in create_refund
ValueError: invalid literal for Decimal: '£45'
```

**After** (tool result with `is_error: true`):

```text
Error: amount must be a number in the order's currency without symbols (e.g. 45.00); got "£45".
Order ord-5521 is in GBP; maximum refundable is 120.00.
```

## 4. Ungated write → scoped, previewable write

**Before:** `execute_sql(query: string)`: the agent can read or change anything the DB user
can.

**After:** narrow tools split by risk.

| Tool | Risk | Behaviour |
|---|---|---|
| `orders_search(customer_email, status, since)` | Low | Read-only, parameterised query, ≤ 50 rows |
| `orders_issue_refund(order_id, amount, reason, dry_run=true)` | High | `dry_run` returns the exact change; real run needs human approval, uses an idempotency key, checks in code that the end user may refund this order, logs the action |

The model never writes SQL, never sees credentials, and can't widen its own scope.

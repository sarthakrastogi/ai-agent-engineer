# Scoping interview

## How to run it

- Read the codebase and docs first; don't ask what you can find out.
- Ask in rounds of 3–5 questions, most decision-relevant first.
- When the user doesn't know, propose a concrete default with a reason ("p95 ≤ 10 s because
  it's interactive — change it if not") and mark it "proposed — confirm with user".
- Ask for **5–10 real inputs with good outputs**. They seed the eval set.
- Stop when you can fill Problem, Success criteria and Scope in `design.md`.

## Question bank

| Area | Ask | Lands in design.md |
|---|---|---|
| Job and users | Who uses it, when? What do they do today, at what cost? The one thing it must get right? Interactive, batch or event-triggered? | Problem |
| Inputs and outputs | What arrives (share real ones)? What comes out: answer, record, action, draft? Consumed by a person, a system (schema), or both? | Problem |
| Correctness | Correct output per example; would two experts agree? Which errors are tolerable vs unacceptable? When unsure: ask, refuse, hand off, or guess and flag? | Success criteria |
| Scope | What must it refuse or hand off (name 3)? Weekly edge cases? Can the output space be fixed (one format, schema, stack)? | Scope |
| Data and tools | What knowledge, where, who grants access, how fresh? Which systems read vs written? PII/regulated data, and where may it be sent or logged? | Architecture → tools, sources |
| Actions and risk | Worst thing it could do if manipulated? Which actions are irreversible, cost money, contact people, touch shared systems? Who approves, how fast? Does it read outside content (web, email, uploads)? | HITL points; Risks |
| Budgets and volume | Tasks/day now and in a year? Latency p50/p95 (first response, end-to-end)? Cost per task; value of one task? | Success criteria |
| Constraints | Required providers, models, clouds, regions, frameworks? Compliance, residency, retention? Deadline and maintainer? | Architecture → models; Decision log |
| Eval data | Logs or historical decisions with known outcomes? Who labels pass/fail, how many hours? | Open questions / `agent-evals` |

Unanswered questions go in Open questions.

## Turning answers into success criteria

Each criterion is a row: **metric + threshold + how graded + on which data**, written so two
people agree whether a run passed.

- **Binary where possible.** Express severity with several binary checks, not one 1–5 scale.
- **Cover every dimension:** quality, safety/scope, format, latency, cost.
- **Say how it's graded:** code check, validated LLM judge (`agent-evals`), or human.
- **Include should-not cases:** out-of-scope requests that must be refused, actions that must
  not run without approval.
- **Name the dataset:** the interview examples, growing to 20–50 tasks from real failures
  before launch.
- **Constrain the output space:** if the user can live with one target (fixed stack, schema,
  template), write it into Scope. It makes prompts, evals and error patterns tractable.
- **Expect drift:** revisit criteria after the first error-analysis round; log changes.

| User says | Write instead |
|---|---|
| "Accurate" | "≥ 90% of eval tickets get the correct category (exact match vs labels, code check)" |
| "Don't make things up" | "≥ 95% of answers cite a retrieved source supporting every claim (validated binary judge)" |
| "Fast" | "p95 time to first token ≤ 1.5 s; p95 end-to-end ≤ 8 s (traces)" |
| "Cheap enough" | "Mean cost ≤ $0.05 per task over the eval set (token accounting)" |
| "Safe" | "0 high-risk actions without approval across eval and red-team sets (code check on traces)" |
| "Handle the weird ones" | "100% of 15 out-of-scope cases refused or handed off (code check on route)" |
| "Good summaries" | "All 4 required fields present and no claim absent from the source (binary judge per field)" |

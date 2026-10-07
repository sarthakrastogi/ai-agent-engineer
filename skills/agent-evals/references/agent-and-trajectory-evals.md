# Agent and trajectory evals

Terms: **task** = one case with spec, fixtures, success condition; **trial** = one
attempt; **outcome** = final environment state (a DB row counts, "I've booked it" doesn't).

## Three levels, in this order

1. **Outcome.** Did the task succeed? Check end state in code. This gates.
2. **Trajectory.** No forbidden or unauthorised calls, within step and token budgets, no
   loops. Diagnosis only, except where the path is itself a requirement (safety, authz,
   cost). Assert required steps actually ran: expected route or model chosen, validation
   step produced a real score (not a default), fan-out happened. A misrouted simple query
   passes every output check and spends ~10× the tokens.
3. **Per-step.** Tool choice, arguments, error handling, context retention, efficiency.
   For localising (`agent-accuracy`), not headline metrics.

Grade outcomes, not exact step sequences; those penalise valid alternatives. Partial
credit only where it reflects real value on multi-part tasks.

## Environment and state

- Every trial starts from a clean, pinned environment (DB snapshot, mocks, temp dir).
- Assert what changed and what must **not** have changed.
- Conversational agents: check state *and* that the final message tells the truth about it.

```python
def grade_refund_task(env, transcript):
    r = env.db.query("select amount, status from refunds where order_id = ?", "A-1009")
    return {
        "outcome": bool(r) and r.amount == 42.00 and r.status == "created",
        "no_double_refund": env.db.count("refunds", order_id="A-1009") == 1,
        "told_user_amount": "42" in transcript.final_message,
        "steps": transcript.n_model_calls, "tokens": transcript.total_tokens,
    }
```

## Tool-call correctness

| Check | Question | Grader |
|---|---|---|
| Selection | Right tool, or correctly none? | Code |
| Arguments | Right values, units, IDs, formats? | Code: schema + value match |
| Preconditions / authz | Was the call allowed now (verified, confirmed, in scope)? | Code over the trajectory |
| Result handling | Read the result correctly; recovered from errors? | Judge or code |
| Resulting state | Did the world end up right? | Code |

Schema-valid ≠ correct. Multi-agent: check **handoff accuracy** (right sub-agent, needed
context passed).

When path matching is needed, use modes: `strict`, `unordered`, `subset` (only allowed
tools), `superset` (at least required tools); argument modes `exact | ignore | subset |
superset | custom`. An LLM trajectory judge is the fallback for "was this path reasonable?".

## pass@k vs pass^k

With `n` trials and `c` successes per task, averaged over tasks:

```python
from math import comb
pass_at_k  = 1 - comb(n - c, k) / comb(n, k)   # P(at least one of k succeeds)
pass_hat_k = comb(c, k) / comb(n, k)           # P(all k succeed)
```

- **pass@k** — "can it ever?" Capability exploration, or when a human/verifier cheaply
  picks the best of k.
- **pass^k** — "every time?" User-facing and reliability-critical flows. 75% per trial →
  pass^3 ≈ 42%.
- Choose k from how often users repeat the task; report pass@1 alongside.
- 95% per step ≈ 60% over 10 steps; long agents need far higher per-step reliability.

## Capability vs regression

| Suite | Starts | Purpose | Gate |
|---|---|---|---|
| Capability | Low | Hill-climb hard tasks | No |
| Regression | Near 100% | Catch breakage | Yes |

Promote tasks that pass reliably; refill capability from production. Read the transcript on
every failure; the cause is often the grader, fixture or spec.

## By agent type

| Agent | Outcome check | Add |
|---|---|---|
| Workflow / pipeline | End-to-end result | Each node on its own I/O; routing correctness per branch |
| Coding | Tests pass, static analysis | Scope-creep rubric; hidden tests; code check for special-cased test inputs or edited tests |
| Conversational / support | Backend state, policy compliance | Simulated users with persona and goal |
| Research | Claims grounded, key facts covered | Citation accuracy, source quality (keep a human sample: judges miss low-quality sources), tool efficiency |
| Computer use / browser | Page + backend state | Step budget, irreversible-action checks |
| Retrieval-heavy | Correct and faithful | Per-retrieval metrics (`agent-rag`) |

## Multi-turn

- Reduce each failure to its simplest reproduction: single turn, or **N-1** (real prefix +
  next turn).
- Whole-conversation evals: LLM-simulated user with persona, goal and hidden facts.
  Validate the simulator against real users first.
- Judge at span (step), trace (turn) or session (coherence) level, wherever the failure
  lives.

## Confidence calibration

When a confidence score drives act / route / escalate:

- Bucket labelled cases by stated confidence; compare mean confidence with observed
  accuracy per bucket.
- Slice by segment; overconfidence often hides in rare cases.
- Measure on your own traffic; re-check after model, prompt or traffic changes.
  Verbalised LLM confidence is not a probability until this passes. Thresholds and
  rollout: `agent-production` → `decision-classifiers.md`.

## Cost per trajectory

Record steps, tool calls, tokens (in/out/cached), wall time and cost per trial. Token spend
explains most performance variance on agentic tasks, so compare versions **at a token
budget**; a "better" agent spending 3× may just be spending more.

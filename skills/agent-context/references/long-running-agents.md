# Long-running agents

## Continuation strategy

| Situation | Strategy |
|---|---|
| Conversation with a human, tone continuity matters | Compaction within one session (`memory-and-compaction.md`). |
| Coding or file-based work spanning windows | Fresh window each session; state rebuilt from files and git. |
| Broad research or parallel investigation | Lead agent plus subagents in clean windows. |
| Unattended batch over many items | One short run per item; pilot on 2–3 items first. |

A fresh window plus good state files often beats compaction: nothing lossy sits between
the agent and the truth.

## Multi-window harness

1. **Initializer session** writes:
   - a task list in JSON, every item `"passes": false`
   - an init script that starts the environment and runs the checks
   - a free-text progress log
   - an initial git commit
2. **Each later session:**
   - reads the progress log, task list and `git log`
   - runs the init script and confirms the environment is healthy
   - picks **one** unfinished item and implements it
   - verifies it end to end with a runnable check (tests, build, fixture diff, screenshot)
   - commits, flips that item's `passes`, appends to the progress log
3. **Ends** when every item passes or a bound is hit.

```json
{
  "tasks": [
    {"id": "auth-01", "desc": "User can log in with email", "passes": false,
     "check": "pytest tests/e2e/test_login.py"}
  ],
  "rules": "Only flip `passes` after the check succeeds. Never edit or delete checks."
}
```

- **One item per session** so the agent doesn't run out of window mid-change.
- **The runnable check prevents premature victory**; without it the agent stops when work
  looks done.
- **JSON for state**; models corrupt it less than Markdown.
- **One commit per unit of work**, prefixed `agent: <summary>` with modified files listed in
  the body, so agent work is filterable and reversible.
- **Guard the checks:** "It is unacceptable to remove or edit tests", enforced with file
  permissions or a hook.
- **Keep the goal in attention:** plan recitation and compaction notice
  (`memory-and-compaction.md`); restate format rules every 3–5 messages on models where
  they fade.
- **Subagents** return ~1–2K-token summaries plus file paths, never transcripts. Briefs,
  one-writer rule, fresh-context review: `agent-design` → `references/multi-agent.md`.

## Bounds

Set in code, not only in the prompt.

| Bound | Setting |
|---|---|
| Max turns / tool calls per run | Always set; size from p95 of successful runs. |
| Consecutive errors before escalation | `agent-production` → `references/reliability.md`. |
| Token and spend cap per run | Required; alert at ~80%. |
| Wall-clock timeout per tool and per run | Per tool; return a timeout as an actionable error. |
| Context ceiling | From the quality-vs-length curve (`context-budget-and-ordering.md`). |

Durable execution (checkpoints, resume from the failed step, idempotent side effects) is
`agent-production`.

## Evaluating long runs

- **Judge the end state** (tests pass, files correct, ticket resolved); add step-level
  diagnostics for efficiency.
- **Include long cases**; short cases hide context failures.
- **Track per run:** success, turns, total tokens, peak context, compactions, cache hit
  rate. Compare before and after every context change (`agent-evals`).

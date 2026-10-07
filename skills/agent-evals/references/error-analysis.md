# Error analysis

Do this before writing any metric or judge, and before buying eval tooling. Expect to
revise failure definitions after every review round.

## 1. Sample ~100 traces for coverage

Over-represent:

- negative feedback, low judge scores, errors, retries;
- cost and latency extremes (very cheap: refusal or early exit; very expensive: loops);
- long multi-turn sessions, rare intents and segments.

Mix: cluster by intent or embedding into 6–10 groups; take 60–70% as cluster
representatives, 30–40% at random. Record the sampling method in `failure-taxonomy.md`.

No traffic yet: run the agent on 20–50 realistic hand-written or synthetic inputs and
analyse those; redo on real traffic as soon as it exists.

## 2. Open coding (30–50 traces)

Read input → every step (model calls, tool calls and results, retrieved chunks) → output.
Per trace write **pass/fail** and **one note on the first upstream failure**; later errors
cascade from it.

- Describe behaviour, don't diagnose: "searched orders by email, user gave an order ID,
  returned 'not found'", not "bad tool design".
- No predefined categories.
- **The domain expert owns the first 30+ codes:** they annotate, or they correct ~30
  drafted notes and review the drafted modes. No taxonomy is used before that review.
- Stop when ~20 traces in a row add no new kind of failure.

```text
trace_id | pass/fail | first upstream failure (observed, specific)
t_0142   | fail      | asked for "last month's invoices"; tool called with no date filter
t_0151   | fail      | refund policy chunk retrieved, answer quoted 30-day window as 60 days
```

## 3. Axial coding into 5–10 modes

Per mode:

- a name that says what broke (`missing_date_filter`, not `information_quality`);
- a one-sentence observable definition two people would apply identically;
- the likely component (retrieval / tool / prompt / reasoning / format / context /
  upstream data); `agent-accuracy` uses this column.

Split a mode when members need different fixes; merge near-duplicates. An LLM may propose
groupings; a human confirms.

## 4. Label and count

One boolean per mode per trace; compute rates. A few modes usually dominate. Rank by
rate × severity. Segment rates (feature × scenario × persona): 10% overall can be 40% for
one tier.

## 5. Agents: transition failure matrix

Tabulate last successful state → first failed state; start with the biggest cell.

```text
             first failure →  ParseIntent  ChooseTool  BuildArgs  ExecTool  Answer
last success ↓
Start                         3            -           -          -         -
ParseIntent                   -            5           -          -         -
ChooseTool                    -            -           12         1         -
ExecTool                      -            -           -          -         4
```

## 6. Taxonomy → decisions

From the highest-rate mode down:

1. **Fixable directly** (missing instruction, tool bug, config) → fix it
   (`agent-accuracy`). Don't build an evaluator for a one-line prompt fix.
2. **Recurs after a fix, or costly enough to guard** → evaluator: code for objective, LLM
   judge for subjective, runtime guard for compliance (`agent-guardrails`).
3. **Needs a product decision** (policy is silent) → flag to the user.

Record it in the `Tracked by eval?` column of `failure-taxonomy.md`.

## Practice

- One domain expert decides what counts as a failure. With several annotators, label a
  shared batch independently and check Cohen's κ before splitting work.
- Build a simple trace viewer: all context on one screen, one-key pass/fail, notes field.
- Under OTel, trace-level I/O can be empty; read and score the child generation span.
- Cadence: weekly until modes stabilise, then monthly, plus after incidents, model changes
  or traffic shifts. Between rounds, read 10–20 outlier traces a week.
- Traces missing tool results or full prompts are an observability gap: fix with
  `agent-observability`.

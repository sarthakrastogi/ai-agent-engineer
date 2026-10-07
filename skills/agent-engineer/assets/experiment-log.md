# <Agent name> — experiment log

Append-only. One entry per behaviour-changing change (prompt, tools, retrieval, model, code
in the agent loop). Record failures too — they stop the team repeating them.

<!-- template:
## YYYY-MM-DD — <short title>
- Change:
- Hypothesis: (which failure mode, why this should help)
- Eval: <suite/command>, dataset <name@version>
- Result: <metric before → after>, regressions: <none / list>
- Cost/latency impact:
- Decision: keep / revert / iterate
-->

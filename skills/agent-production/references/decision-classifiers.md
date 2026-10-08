# Decision classifiers

Replace frontier-LLM calls that only *decide* with cheap typed classifiers. A decision
qualifies when the answer is a fixed set, yes/no or a score; volume or latency matters; and
you can label 100–200 cases. Leave reasoning and writing to the LLM.

## Options

| Option | Use when | Watch |
|---|---|---|
| Code / rules | Condition is deterministic | Always try first |
| Small LLM, constrained output (enum/schema) | Quick start, few labels | Verbalised confidence isn't a probability; use token logprobs where exposed, and calibrate |
| Fine-tuned small classifier | High volume, stable labels, labelled data | Poor out-of-domain generalisation (`agent-guardrails` → `references/input-output-guards.md`) |
| Hosted typed decision model | Many decision types, no training | Generic calibration; pin the version; measure on your data |

## Where they fit

| Decision point | Question shape | Act on it | Notes |
|---|---|---|---|
| Intent routing | One of N handlers + `other` | Route; low confidence → person or LLM path | Savings come from branches needing no LLM (order status → DB lookup) |
| Model routing | Small/large or difficulty score | Cheapest model whose route passes evals | Router must cost far less than it saves; sweep effort first (cost-and-latency.md) |
| Input / tool-result screening | Yes/no per category + harm score | Thresholds in code | A filter, not a security boundary; keep least privilege underneath. Track false blocks |
| Tool-call gating | "Is this action consistent with the user's task?" | Allow; block with reason so the agent re-plans; human after repeated blocks | Feed only the task and pending action, never tool outputs, so injected content can't argue. Design: `agent-guardrails` |
| Output verification | Grounded? All sub-questions answered? Policy OK? | Send / retry once / escalate | Synchronous; online judges are async triage (`agent-evals`) |
| Escalation | Confidence band | High → act; medium → gather context, retry (bounded); low → person | Automate only reversible actions on high confidence |

## Writing the questions

- One judgment per question; combine several in code.
- Write the exact condition: scoping words and negations are read literally.
- Criteria, not degrees ("broken feature, workaround exists", not "moderate").
- Always offer an exit (`other`, `unclear`).
- A yes/no at 0.5 means "can't tell". For a spectrum, ask for a score.
- Math, dates and counting stay in code; to count items meeting a condition, ask yes/no per
  item and sum.
- Send only the state the question needs.

## Thresholds and calibration

- Set thresholds per decision from the cost of each error type, after measuring. 0.6 for
  routing to a person is a placeholder until you have labels.
- Use three bands (act / gather more / escalate) where a middle path exists.
- Check calibration on your labelled traffic: per confidence bucket, observed accuracy ≈
  stated confidence (`agent-evals` → `references/agent-and-trajectory-evals.md`).
- Evaluate like a judge: labelled set, TPR/TNR per class, re-check after model, prompt or
  traffic change.
- Put classifier version, threshold and confidence on the span.

## Rollout

1. Pick one decision the agent already makes.
2. Shadow: run beside current behaviour, log answer, confidence, version; don't act.
3. Label 100–200 shadowed cases; compare accuracy, latency, cost per solved task. Tune
   thresholds; pin the version.
4. Automate only where accurate: high confidence on reversible actions; rest to a person
   or stronger model.
5. Log the result (`experiment-log.md` if used); keep monitoring band accuracy online.

## Keep out of a classifier

- Anything that generates text; arithmetic, counting, dates.
- Modalities it wasn't built for.
- Low-volume, high-cost decisions (use a reasoning model plus a person).
- Being the only security boundary.

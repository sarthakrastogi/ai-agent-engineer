# Localising failures

First name the failing layer of the agent stack (`agent-design` → `the-agent-stack.md`)
and fix at the lowest layer that explains the failure. Then find the component below.

## Find the first upstream failure

Read the trace in pipeline order; stop at the first step whose output was wrong given its
input:

1. **Input**: ambiguous, out of scope, missing info? (Then the failure is not asking or
   refusing.)
2. **Understanding / plan**: task and constraints identified?
3. **Tool selection**: right tool, or correctly none?
4. **Arguments**: values, IDs, units, date ranges?
5. **Tool result**: succeeded and returned what was needed?
6. **Retrieved context**: was the needed fact in the window at all?
7. **Generation**: used what was there, faithfully?
8. **Format / post-processing**: parsing, validation, rendering?
9. **Grader**: is the verdict right? Check this early.

Many traces of a multi-step agent: build the transition failure matrix (`agent-evals` →
`error-analysis.md`, step 5) and start with the biggest cell.

If the trace doesn't show a step (no tool result, truncated prompt, no chunks), fix
instrumentation first (`agent-observability`).

## Symptom → component → confirm

| Symptom | Likely component | Confirm by |
|---|---|---|
| Confident wrong fact | Fact missing/stale in context, or present but ignored | Search context. Absent → retrieval/data; present → generation |
| Contradicts retrieved context | Distractors, fact buried mid-context, no "only from context" rule | Re-run with only the gold chunk |
| Invented citation, ID, URL | No grounding; IDs not passed through | Code check: cited IDs ⊂ retrieved IDs |
| Answers when it should abstain or ask | No permission to abstain; no answerability check | Add the abstain rule on failing cases as a probe |
| Wrong tool | Overlapping names/descriptions, too many tools | Selection check over the set; compare competing descriptions; re-run with fewer tools |
| Right tool, wrong args | Ambiguous schema, missing format guidance, value not in context | Argument check; confirm the value was in context |
| Tool error → gives up or loops | Unhelpful error, no recovery guidance | Replay with mocked error + actionable message |
| Misreads a successful result | Bloated or ambiguous response shape | Replay with trimmed, labelled response |
| Says "done", state unchanged | Silent failure, no verification | State check vs final message |
| Confident answer after empty/`null`/truncated tool result | Error never reached the model | Read the tool span; replay with explicit error. Fix in tool (`agent-tools`), flag on span (`agent-observability`) |
| Answers part of a multi-part question | No decomposition; faithfulness can't see the missing half | Per-sub-question completeness check; re-run split |
| Ignores an instruction | Contradiction, buried position, vague wording, long prompt | Search for conflicts; ablate sections; move it |
| Format breaks | No structured output or validation | Schema-validation pass rate |
| Different results across runs | Ambiguity, borderline case, sampling | k ≈ 3/q trials; diff a passing and failing run to find divergence |
| Degrades late in long sessions | Context rot, facts lost in compaction | Failure rate by turn or context length; N-1 with trimmed history (`agent-context`) |
| Worse after model upgrade | Prompt tuned to old model; changed defaults | Paired run of both models, sliced by mode |
| Worse after re-indexing | Retrieval regression | Recall@k on fixed labelled queries before/after (`agent-rag`) |
| Fine on evals, bad in prod | Dataset ≠ traffic | Compare tag mix vs production sample |
| Sub-agent fine, final answer wrong | Lossy handoff | Inspect the handoff payload |
| Eval fails, output looks right | Grader bug, stale reference | Read transcript; check judge TPR/TNR |

## Counterfactual probes

Change one thing, re-run the failing cases k times. Probes are diagnostic; revert after.

| Probe | Do | If it now passes |
|---|---|---|
| Oracle context | Insert the gold fact by hand | Retrieval/data is the cause; still fails → generation or instructions |
| Oracle tool result | Replay the prefix with the correct tool result | Tool or its arguments |
| Replay from checkpoint | Fix the first wrong step by hand, continue | Downstream is fine; fix only that step |
| Ablation | Remove a prompt section, tool or old history | That element interfered |
| Stronger model | Same prompt/context, most capable model, high effort | Possible capability limit (check cheaper rungs first); still fails → spec, context or task |
| Clarified spec | Add an explicit instruction for this case | Instruction missing or ambiguous; fix it generally |

Replays need traces with full prompts, tool calls and results; if missing, that is the
first fix.

## Capability or reliability

Run each failing case k ≈ 3/q times (`experiment-discipline.md`). Too few runs make a 10%
failure look fixed.

| Pattern | Problem | Fix |
|---|---|---|
| 0/k | Capability or deterministic bug | Find the missing context, tool or instruction; model change only after |
| Some of k | Reliability | Remove ambiguity, borderline examples, rules into code, verification, smaller decision space |
| High pass@k, low pass^k overall | Reliability everywhere | As above; gate on pass^k |
| Low pass@k overall | Capability everywhere | Re-check spec and grader, then climb the ladder |

A bigger model rarely fixes reliability. A model change is justified for capability
failures with clean context and instructions.

## RAG: retrieval vs generation

1. Gold chunk **missing** from top-k → retrieval: coverage, chunk boundaries, lexical
   mismatch (add BM25), missing filters, ranking.
2. Gold chunk **present**, answer wrong → generation: faithfulness, mid-context burial,
   distractors, "only from context, else unknown".
3. **Faithful but unhelpful** → relevance or answerability: abstain or escalate.

Depth: `agent-rag` → `diagnosing-rag.md`; delegate to `rag-diagnostician` if available.

## Rule out the eval

- Is the reference or expected state right?
- Would the expert agree with the verdict?
- Is the task possible with the agent's tools and data? 0% over many trials is usually a
  broken task.

A grader fix is a legitimate result; log it.

With many failing traces, delegate to `trace-analyst` (modes, counts, component per mode).
Otherwise run this on 30–50 failing traces and fill the `Component` column of
`failure-taxonomy.md`.

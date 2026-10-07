# Workflow patterns

Patterns compose: a router can send one branch to a chain and another to an agent. Make
every edge that can be a code check a code check.

## Choosing

| Pattern | Use when | Cost / latency vs single call |
|---|---|---|
| Single call | One input → one output; knowledge fits in prompt or retrieval | 1x |
| Prompt chaining | Fixed, separable subtasks; you want to inspect intermediates | N calls, serial |
| Routing | Distinct input categories; easy ones can go to a small model | ~1x + cheap classifier |
| Parallelisation | Independent subtasks (sectioning) or several attempts (voting) | N calls, parallel |
| Orchestrator-workers | Subtasks unknown until the input is seen | Variable |
| Evaluator-optimizer | Clear criteria; critique measurably improves output | 2–3x per round |
| Agent loop | Path depends on intermediate results | Unbounded unless capped (~4x chat) |
| Plan-then-execute | Real side effects users must approve first | + read-only pass and a human wait |

- Pick the cheapest row that meets the success criteria on the eval set.
- Before any LLM step, ask whether code can do it.
- Count **evaluation burden** as a cost: a workflow is testable per node and route; an agent
  needs end-to-end trajectory evals. Choose the agent loop only when tool selection can't be
  anticipated or the paths are too many to maintain as a graph.

## Single call

- **When:** classification, extraction, summarisation, Q&A over provided text. Usually
  enough; try it first and measure.
- **Pitfalls:** skipping it because it feels too simple; stuffing the prompt instead of
  retrieving.

```text
docs = retrieve(query, k=5)                     # optional
out  = llm(system, examples, docs, query, schema=OutputSchema)
validate(out)                                   # code check, not another LLM
```

## Prompt chaining

- **When:** fixed steps each easier than the whole (extract → normalise → validate), or you
  need to inspect intermediates.
- **Shape:** sequential calls with a **code gate** between steps that stops or retries early.
- **Pitfalls:** no gates, so one bad step poisons the rest; chaining what one call does as
  well; passing full history instead of what the next step needs.

```text
outline = llm(p_outline, input)
if not gate_outline(outline): return fail("outline", outline)
draft   = llm(p_draft, outline)
return llm(p_polish, draft)
```

## Routing

- **When:** distinct categories handled differently, or difficulty varies enough to send
  easy inputs to a small model.
- **Shape:** classifier picks a handler with its own prompt, tools and model. **Code or rules
  for exact categories** (field value, keyword, form choice); **LLM with enum output only for
  semantic ones**.
- **The router must cost less than it saves.** An LLM router adds 1–5 s, doubling short
  requests. Prefer code or a small classifier with an `other` route and a confidence score;
  send low confidence (threshold measured on labelled data) to a human or the general
  handler (`agent-production` → `references/decision-classifiers.md`). If one route takes
  ~90% of traffic, make it the default in code and classify only the rest.
- **Pitfalls:** no `other` route; router accuracy never measured on its own; overlapping
  categories that route differently on reruns.

```text
route = classify(input, labels=["refund", "tech", "other"])   # enum / structured output
return HANDLERS.get(route, HANDLERS["other"])(input)
```

## Parallelisation

- **Sectioning:** independent subtasks at once (guardrail screen beside the answer;
  separate prompts per aspect).
- **Voting:** same task several times, aggregate, when a false negative is costly.
- **Best-of-N:** subjective outputs with wide spread (UI, copy); keep the best by a check or
  human pick.
- **Shape:** fan out, aggregate in code (majority, any-flag, threshold).
- **Pitfalls:** sections that aren't independent; LLM aggregation where code would do; a
  parallel guardrail that fires after side effects. Run it blocking before any action
  (`agent-guardrails`).

```text
results = parallel([llm(p_answer, x), llm(p_safety, x)])
if results.safety.flagged: return refuse()
return results.answer
```

## Orchestrator-workers

- **When:** subtasks depend on the input (which files to change, which sources to search).
- **Shape:** orchestrator plans subtasks as structured output; code dispatches workers;
  a synthesiser combines.
- **Pitfalls:** one-line briefs (use the delegation brief in `multi-agent.md`); workers
  returning transcripts instead of distilled results; no subtask cap.

```text
plan = llm(p_plan, input, schema=list[Subtask])[:MAX_SUBTASKS]
outs = parallel(worker(t.brief) for t in plan)
return llm(p_synthesise, input, outs)
```

## Evaluator-optimizer

- **When:** clear criteria, feedback measurably improves output, and something can give that
  feedback (tests, a validated judge).
- **Shape:** generate → critique → revise until pass or `MAX_ROUNDS`. Prefer deterministic
  evaluators (tests, linters, schema checks) over an LLM.
- **Pitfalls:** no round cap; an LLM evaluator never validated against human labels
  (`agent-evals`); criteria broader than requirements (over-engineering); oscillation.

```text
out = llm(p_generate, task)
for _ in range(MAX_ROUNDS):
    verdict = run_tests(out) or llm_judge(criteria, out)
    if verdict.passed: return out
    out = llm(p_revise, task, out, verdict.feedback)
return escalate(out, verdict)
```

## Agent loop

- **When:** steps can't be predicted, the agent can get ground truth from the environment
  each step, and compounding cost and error are acceptable.
- **Shape:** gather context → act → verify → repeat. Your code owns the loop: tool calls are
  structured outputs your code executes, so it can interrupt for approval or compaction.
- **Before it ships:** loop essentials in `the-agent-stack.md`.
- **Pitfalls:** no turn cap; no runnable verification, so it stops "when it looks done";
  errors hidden from the model; long focused runs past ~10–20 steps without decomposition.

```text
for turn in range(MAX_TURNS):
    resp = llm(context, tools)
    if not resp.tool_calls: break
    for call in resp.tool_calls:
        if risk(call) == HIGH and not await approval(call):
            context.append(rejected(call)); continue   # model sees the rejection
        context.append(execute(call))            # timeout, errors visible
    context.append(run_checks())                 # tests / lint / schema as feedback
    if hard_blocker(context) or too_many_errors(context):
        return escalate(context)
```

Define exits explicitly: final-output tool or schema, no tool call, unrecoverable error,
turn cap, cost cap.

## Plan-then-execute

- **When:** the agent writes files, runs migrations or deploys, and users must see what will
  happen first, or the request is ambiguous.
- **Shape:** **Plan** mode has read-only tools, asks questions, writes a plan file
  (decisions, assumptions, ordered steps); the user edits and approves. **Execute** gets
  write tools and follows the plan; deviations go back to the user.
- **Pitfalls:** plan mode enforced only in the prompt (remove write tools in code); plans too
  vague to check execution against; re-planning every turn on small tasks.

```text
plan = agent(task, tools=READ_ONLY)                 # may ask questions; writes plan.md
if not await approval(plan): return revise_or_stop(plan)
return agent(task, plan, tools=READ_ONLY + WRITE)
```

## Human approval gate

- **When:** before high-risk actions (irreversible, financial, external messages, shared
  systems), on repeated failures, on out-of-scope requests.
- **Shape:** "contact a human" is a tool. On a gated call, persist run state, notify, stop
  using compute, resume on approve/reject (SDK interruption + serialised state, or a
  durable-execution wait step).
- **Pitfalls:** approvals on low-risk calls (fatigue); UI hiding the exact arguments;
  resuming from client-supplied state; the LLM deciding whether approval is needed.

```text
if call.tool in HIGH_RISK or call.cost > LIMIT:
    state_id = persist(run_state)
    notify_approver(call.tool, call.args, state_id)
    return PAUSED                                 # resume(state_id, decision) later
```

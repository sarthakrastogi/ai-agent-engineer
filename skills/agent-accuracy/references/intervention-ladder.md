# The intervention ladder

code/config/data → prompt → examples → tools → retrieval → architecture → model →
fine-tune. Each rung costs more, touches more behaviour and is harder to attribute.

**Climb only with evidence:** a fix at the current rung failed *and* localisation points
higher. Skip rungs only when localisation is unambiguous (oracle context passes → go
straight to retrieval).

**Match the axis first.** *Context* problems (what the model must know) → retrieval, data
tools, context assembly. *Behaviour* problems (format, consistency, style, policy) →
instructions, examples, structured output, fine-tuning. A context fix for a behaviour
problem can lower accuracy.

## 0. Code, config, data

- **When:** tool bug, wrong parameter mapping, parse error, stale/missing data, wrong
  prompt version loaded, timeout swallowed as an empty result.
- **How:** call the function directly with the failing input to reproduce, fix, call
  again to confirm, then add a unit test and the eval case to regression.
- **Pitfall:** prompting around a bug ("if the tool returns nothing, try again"). Many
  "LLM failures" are plain bugs.

## 1. Prompt instruction

- **When:** a requirement is missing, ambiguous or contradicted; no permission to abstain
  or ask; failure recurs across a category.
- **How:** general rule plus its reason ("amounts come from the order record, never the
  user's message, because users misstate them"). Remove conflicting lines. Depth:
  `agent-prompting`.
- **Pitfalls:** a line per bad trace; CRITICAL/MUST walls that over-trigger; wording copied
  from eval cases.

## 2. Examples

- **When:** instructions are clear but format or borderline behaviour still fails.
- **How:** 3–5 diverse, canonical examples including the borderline, never from eval
  dev/test. For complex tool inputs, add tool input examples.
- **Pitfalls:** near-identical examples copied verbatim; repetitive history that few-shots
  the agent into drift; examples encoding an eval case.

## 3. Tools

- **When:** wrong tool, wrong arguments, misread results, poor error recovery.
- **How:** sharper names and descriptions, enums/formats/units in schemas, merge
  overlapping tools, actionable errors, concise responses, tool search for large sets.
  Overlap matters more than count. Tool quality often matters more than the system prompt.
  Depth: `agent-tools` → `tool-definition-checklist.md`.
- **Pitfalls:** adding a tool to fix tool confusion; raw API dumps as results; prompt prose
  that belongs in the tool description.

## 4. Retrieval and context

- **When:** the needed fact was absent from context on failing traces and oracle context
  passes; or long runs lose facts to compaction or burial.
- **How:** validate recall@k on labelled queries before touching generation; then
  chunking, hybrid search, filters, reranking (`agent-rag`). Long runs: budgeting,
  compaction, just-in-time retrieval (`agent-context`).
- **Pitfalls:** RAG for a behaviour problem; stuffing more chunks (accuracy falls with
  context length); tuning generation before measuring retrieval; no retrieval logs.

## 5. Architecture

- **When:** separable steps with different failure modes, distinct intents one prompt
  can't serve, or errors a verification step could catch. Only if it demonstrably improves
  outcomes.
- **How:** chaining with checks between steps; routing to specialised prompts; a verifier
  with a runnable check (tests, schema, state diff) and bounded retry; must-hold rules in
  code. Verification strength: code/rules > visual checks > LLM judge. Known steps → a
  workflow, not an agent. Depth: `agent-design`.
- **Pitfalls:** multi-agent for a prompt problem; every handoff loses context; unmeasured
  latency and cost; a verifier with no criterion.

## 6. Model or reasoning effort

- **When:** cases pass 0/k with oracle context, clean instructions and good tools, and a
  stronger-model probe passes.
- **How:** effort sweep, then step-down/up order per `agent-design` →
  `references/model-and-framework-choice.md`. Compare models paired on the full suite with
  cost and latency, at matched token budgets. Re-tune the prompt for the new model.
  Migration and rollout: `agent-production`.
- **Pitfalls:** a bigger model for a reliability or spec problem; ignoring the agreed cost
  and latency.

## 7. Fine-tuning

- **When:** consistent behaviour, format or style at volume; prompting and examples have
  plateaued; or a small model must match a large one on a narrow, hot-path task (query
  parsing, routing, classification) where an API call costs too much latency. Start with
  50+ high-quality examples and a stable eval.
- **How:** train on validated traces, never eval cases; compare against the best prompted
  baseline, not the original.
- Small classifiers (guard, router, output check) are where it most often pays off;
  training procedure in `agent-guardrails` → `input-output-guards.md`.
- RL from production traces only once a validated grader can serve as reward; a bad reward
  is optimised faithfully.
- **Pitfalls:** fine-tuning to add knowledge (use retrieval; it can make hallucinations
  more confident); before evals exist; leaked eval cases; a hybrid of fine-tuned style +
  retrieved facts without proving both are needed; locking to a retiring snapshot.

## When the popular fix is wrong

| Proposed fix | Wrong when | Do instead |
|---|---|---|
| Add RAG | Fact already in context; failure is format, policy or consistency | Prompt, examples, structured output |
| Bigger model | Passes some of k; ambiguous instruction; confusing tool; fact missing | Rungs 1–4; stronger-model probe before switching |
| Multi-agent | One agent with better tools or a verifier would do; subtasks not independent | Single agent + verification, or a workflow |
| Fine-tune | Missing knowledge, or no eval to show the gain | Retrieval; build the eval |
| Prompt optimiser | Eval small, unvalidated or unrepresentative | Fix the eval first |

## Reliability fixes (passes some of k)

Aim at pass^k, not pass@1:

- Borderline case gets an explicit rule and an example.
- Shrink the decision space: enums, fewer tools, fixed workflow for known steps.
- Must-hold rules into code: validation, guards, deterministic routing.
- Verification step with a runnable check and bounded retry.
- Lower temperature where allowed; reduces variance, not ambiguity. Measure pass^k anyway.
- Voting / self-consistency: k× cost and latency; only if the user accepts it.
- **Confidence-gated escalation:** high → act (reversible actions only); medium → gather
  context and retry, bounded; low → hand off. Calibrate bands first (`agent-production` →
  `decision-classifiers.md`).

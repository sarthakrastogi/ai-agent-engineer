# System prompt structure

Model-specific wording is in `model-quirks.md`.

## Section order

Delimit sections with XML tags or Markdown headings; pick one per prompt.

| # | Section | Contents |
|---|---|---|
| 1 | Role & objective | Who it serves, the job, what "done" means. One short paragraph. |
| 2 | Context | Stable facts needed every turn: domain, users, systems, glossary. Volatile facts are fetched with tools. |
| 3 | Instructions | Heuristics and the routine. Number procedural steps. |
| 4 | Tool policy | Which tool when, act vs suggest, parallel calls, when to ask the user. |
| 5 | Constraints | Scope limits, refusal and hand-off conditions, reversibility, each with its reason. |
| 6 | Output format | Shape, length, register. A schema if code reads it. |
| 7 | Examples | 3–5 canonical cases in `<example>` tags. |
| 8 | Final reminders | Optional: one or two lines restating the most-missed rule, for long prompts. |

- **Stable first, variable last**, so the prefix caches (`agent-context` →
  `references/prompt-caching.md`).
- **Long documents (20K+ tokens) first, query last.**
- **Match prompt style to wanted output.** A Markdown-heavy prompt pulls output toward
  Markdown.

## Altitude

| Too low (brittle) | Right | Too high (vague) |
|---|---|---|
| "If the user says 'refund' and the order is < 30 days and not digital, call `refund`; else if …" | "Refund orders under 30 days old without asking. For digital goods or older orders, explain the policy and offer escalation. The goal is to resolve the issue, not defend the policy." | "Handle refunds appropriately and be customer-focused." |

- **Convert SOPs into numbered routines**, one action per step, with explicit branches for
  missing information ("If the order ID is missing, ask for it. Don't search by name.").
- **Find contradictions by asking the model** "what in this prompt is ambiguous or
  contradictory?", then confirm fixes with evals.
- **Metaprompt with the failure, not the wish:** "The desired behavior is [DESIRED], but
  instead it [UNDESIRED]. What minimal edits would encourage the agent to address these
  shortcomings?" Verify suggested edits with evals.

## Skeleton

Delete any section with nothing real to say.

```markdown
<role>
You are <agent> for <users>. Your job: <outcome>. You are done when <observable end state>.
</role>
<context>
<stable domain facts, glossary, systems; only what every turn needs>
</context>
<instructions>
1. <first step>. If <missing info>, <what to do>.
2. <next step> — because <reason>.
Heuristics: <2–4 judgement rules with reasons>.
</instructions>
<tool_policy>
Use <tool_a> when <situation>; use <tool_b> for <other situation>.
Make independent tool calls in parallel. Never guess missing parameters; ask instead.
Do reversible, local actions freely; ask before <destructive or external actions>.
</tool_policy>
<constraints>
Out of scope: <topics> → <hand-off or refusal wording>, because <reason>.
</constraints>
<output_format>
<shape, length, register; or "Respond using the provided schema.">
</output_format>
<examples> <example>…</example> </examples>
```

## Tool steering

- **State the action mode.** "Suggest changes" yields only suggestions on literal models.
  Say whether to act by default or wait for instructions.
- **Agentic reminders** (strong on literal models; measure on yours): "Keep going until the
  user's query is completely resolved." "If unsure, use your tools to check; do not guess
  or make up an answer." "Plan before each function call and reflect on the results."
- **Eagerness dials.** Less exploration: a call cap ("at most 2 tool calls"), early-stop
  criteria, permission to proceed under uncertainty. More: "don't stop at uncertainty;
  research or deduce the most reasonable approach".
- **Parallel calls:** "Make all independent tool calls in parallel. Never use placeholders
  or guess missing parameters." This pushes parallel calling close to 100%.
- **Search:** start broad, then narrow.
- **Reversibility:** local, reversible actions freely; ask before destructive or shared
  actions; enforce in code too (`agent-guardrails`).
- **Orchestrators:** effort-scaling rules and an over-delegation damper go in the lead's
  prompt (`agent-design` → `references/multi-agent.md`).

## Reasoning

- **Use native controls first:** thinking/`effort` on Claude, `reasoning_effort` on OpenAI.
  Treat effort and `max_tokens` as ceilings. Sweep order: `agent-design` →
  `references/model-and-framework-choice.md`.
- **"Think" tool or scratchpad step** only for policy-heavy sequential tool chains, and
  only with domain examples of how to think.
- **At minimal/low effort**, add an explicit "plan, then act" step.
- **Interleaved reflection:** "After receiving tool results, reflect on their quality and
  decide the next step before proceeding."
- **Self-rubric for zero-to-one builds:** "First create a rubric (5–7 categories) for a
  world-class solution, then iterate internally until it scores top marks." Helps some
  models, confuses others; keep only if evals improve.
- **Against overthinking:** "Choose an approach and commit to it; revisit only when new
  information contradicts it."

## Prompts as code

- **One file per prompt** (`prompts/<agent>/system.md`, or a template with named
  variables), loaded by name. No prompts assembled from fragments across modules.
- **Version every prompt** (semver or content hash in front matter or filename); bump on
  any change.
- **Record the version on each LLM span:** `gen_ai.prompt.name` / `gen_ai.prompt.version`,
  or OpenInference `llm.prompt_template.{template,variables,version}`. Without it a
  regression can't be tied to a prompt change.
- **Review prompt diffs like code** with the eval delta on the PR.
- **Back-test** every change against a library of past production queries, not only the
  failing case.
- **Variants are variables, not forks.** One template with `{policy}` / `{tone}` slots;
  copied prompts drift.
- **Prompt management tools** are optional. If used, pin the fetched version and keep a
  copy in git so evals reproduce.

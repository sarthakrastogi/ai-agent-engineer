# Examples and structured output

## Few-shot examples

Add examples when instructions are clear but format or borderline behaviour still fails
(rung 2 of the fix ladder, `agent-accuracy`).

- **3–5 examples** in `<example>` tags inside an `<examples>` block.
- **Canonical, not exhaustive.** Each shows a *kind* of case: typical, borderline, missing
  information, refusal or hand-off.
- **Vary surface features** (length, wording, entities). Near-identical examples get copied
  literally.
- **Audit every detail.** One flawed example can set the pattern for the whole
  conversation; typos and sloppy edge handling get reproduced.
- **Show the full behaviour:** reasoning field, tool calls and final output in the real
  format.
- **Label non-obvious purpose:** `<example type="missing_order_id">`.
- **Draw from real traffic**, edited for clarity. Synthetic-only examples overfit to how
  you imagine users write.
- **Never use eval dev/test items.** Keep a separate pool, or the score measures
  memorisation.
- **Re-run the whole suite** after adding or changing an example; examples shift behaviour
  globally.
- **Complex tool inputs:** put examples on the tool definition (`input_examples` on
  Claude), not in the system prompt (`agent-tools`).

## Structured output

If code parses the output, use provider schema enforcement. If a human reads it, describe
the format and show an example.

| Need | Use |
|---|---|
| JSON object for the application | Structured outputs with a JSON Schema (`strict` on OpenAI). |
| Model calls a function | Strict tool use with `tool_choice: auto`. Forced `tool_choice` fails on some Claude models (`model-quirks.md`). |
| Classification / routing label | `enum` field or enum-typed tool argument, always with `other`. One judgment per question, criteria not degrees, arithmetic and dates in code (`agent-production` → `references/decision-classifiers.md`). |
| Free text with light structure | Format instructions plus an example. No schema. |
| Answers with citations | Claude's Citations API can't be combined with structured outputs. Choose one. |

### Schema design

- **Make invalid states unrepresentable:** enums over free strings, required fields, `null`
  for "not found" (not `""`). Intern test: could a new hire fill it correctly from field
  names and descriptions alone?
- **Describe every field.** Descriptions are instructions at the point of use.
- **Reasoning field first.** Put a short `explanation`/`critique` before `answer`/`verdict`;
  fields generate in order.
- **Shape it around what the consumer executes.** If code writes files or runs SQL, make
  those first-class (`files: [{path, content}]`, `sql: [...]`) so one response is a complete
  instruction set. Prose with code blocks gives inconsistent delimiters, ambiguous paths
  and truncated files.
- **Don't make the model fill what code knows** (IDs, timestamps, user name). Merge in code.
- **Extraction: emit only what the input states.** Unmentioned fields stay absent or
  `null`, never inferred. Use one fixed operator vocabulary (`lt:200`, `gte:4`, `ne:black`,
  `between:100:200`) that code translates per backend. Measure key F1, value accuracy and
  parse rate on a labelled set (worked example: `agent-rag` →
  `references/retrieval-and-ranking.md`).
- **Check provider schema support** before using `pattern`, `oneOf`, recursion or numeric
  bounds; unsupported keywords are rejected or ignored.

## Validation and retry

Schema enforcement guarantees syntax, not meaning. Treat output as untrusted.

```text
for attempt in 1..MAX_RETRIES (2–3):
    out = llm(prompt, schema)
    if out.refusal:            return fallback(out)        # handle explicitly
    errs = validate(out)       # schema + semantic: IDs exist, dates sane, enum in policy
    if not errs:               return out
    prompt = prompt + f"Your last output failed: {errs}. Fix only these fields."
raise OutputInvalid(out, errs)  # surface it; never silently coerce
```

- **Semantic checks, not just syntax:** referenced IDs exist, cited sources are in the
  retrieved set, amounts are within policy.
- **Feed back specific errors** ("`date` must be ISO-8601, got 'next Tuesday'"), not
  tracebacks.
- **Bound and log retries.** A rising retry rate is an early warning of a bad prompt change
  or model update; track it in `observability.md`.
- **Route refusals to a fallback**, never the parser.
- **Every class of semantic failure becomes a code grader** in `eval-plan.md`
  (`agent-evals`).

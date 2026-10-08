# Prompt review checklist

Report each failed item with the line it refers to and a concrete rewrite. Don't rewrite
the whole prompt unless asked.

## Before reading

- [ ] An eval exists. If not, for a non-trivial change propose the smallest eval that
  would show it worked (`agent-evals`); if declined, say plainly the review is unevaluated.
- [ ] Target model and provider are known (`model-quirks.md`).
- [ ] You have read 10–20 real traces. Trace evidence outranks inference from the text.

## Structure

- [ ] Role and objective state who it serves, the job and what "done" looks like.
- [ ] Sections are delimited (XML or headings) and consistent.
- [ ] Stable content before variable; no timestamp, request ID or per-user data at the top.
- [ ] Long documents first, question last.
- [ ] Output format is stated and matches the consumer (human, code, agent).

## Altitude and clarity

- [ ] Newcomer test: a capable colleague could follow it without questions.
- [ ] No nested if/else trees: heuristics with reasons, numbered routines, or routed
  prompts.
- [ ] No platitudes ("be helpful", "be accurate").
- [ ] Non-obvious rules carry their reason; instructions say what to do.
- [ ] No contradictions (e.g. "be concise" vs "explain thoroughly", "always ask" vs "act
  autonomously").
- [ ] At most one emphasised line; no CRITICAL / MUST / NEVER walls.
- [ ] Prune test: every line would cause a mistake if removed.
- [ ] Must-always rules are enforced in code; the prompt only explains them.

## Tools and actions

- [ ] Cross-tool policy is in the prompt; per-tool detail is only in tool descriptions.
- [ ] Action mode is explicit: act by default, or suggest and wait.
- [ ] Destructive or external actions need confirmation, enforced outside the prompt too
  (`agent-guardrails`).
- [ ] Missing information → ask or search; guessing parameters is forbidden.
- [ ] Stop conditions: when done, when to escalate or hand off.
- [ ] Tools go through the API `tools` field, not pasted into the prompt.
- [ ] Coding against tests: asks for a general solution; tests check the work, not define
  it.
- [ ] If ambitious or comprehensive output is wanted, the prompt asks for it.

## Examples and output

- [ ] ≤ 5 examples, diverse, canonical, in tags; none from the eval dev/test split.
- [ ] Machine-read output uses structured outputs or strict tools, with validation and
  bounded retry in code.
- [ ] No last-turn prefill on Claude 4.6+; no step-by-step reasoning requested inside tool
  arguments.

## Reasoning

- [ ] Depth set with native thinking/effort; a "think" step only where measured to help.
- [ ] No "think step by step" boilerplate on a reasoning model at high effort.

## Safety and data

- [ ] No secrets, credentials or internal URLs; assume the prompt can be extracted.
- [ ] Untrusted content (retrieved docs, tool output, user files) is delimited and labelled
  as data. That is not a security boundary on its own (`agent-guardrails`).
- [ ] Out-of-scope requests have a defined response.

## As code

- [ ] Versioned file, loaded by name; version recorded on traces.
- [ ] Variants are template variables, not forks.
- [ ] The change records its eval delta (`experiment-log.md` if used).

## Report format

Worst first:

| # | Item | Evidence (line / trace) | Rewrite | Expected effect | How to verify |
|---|---|---|---|---|---|

Close with the one change to make first and the eval that would confirm it.

# Authoring guide

Rules for anything under `skills/` and `agents/`. The reader is a capable coding model,
so write only what changes how it does the work.

## Skill layout

```
skills/agent-<topic>/
  SKILL.md        always loaded when the skill triggers
  references/     depth, loaded on demand (one level deep)
  assets/         templates copied into the user's project
```

Don't put runnable app code in a skill. Use short snippets only, and only when they show a
shape the agent needs: a schema, a judge prompt skeleton, span attributes.

## Frontmatter

Use spec fields only (agentskills.io), so every harness can parse the skill:

```yaml
---
name: agent-evals            # same as the directory name
description: >-              # ≤ ~600 chars. This decides whether the skill triggers.
  <What it does>. Use when <concrete triggers>. Not for <neighbour> (use agent-x).
license: MIT
metadata:
  version: 0.1.0
---
```

## Budgets

| Item | Limit |
|---|---|
| `SKILL.md` | < 8,000 B whole file, ≤ 7,400 B body. Aim for ~5 KB (Codex truncates inline skills at 8,000 B). |
| Reference file | ≤ ~250 lines. Merge any file under ~30 lines into another. |

## What stays

- Directives: "do X when Y". Give a reason only when the reason changes behaviour.
- Decision rules, tables, checklists and numbered procedures.
- Numbers that change a decision: thresholds, sizes, counts, budgets.
- Anti-patterns that experienced engineers actually see.
- Pointers to other skills (`agent-x` → `references/y.md`) instead of repeating them.

## What goes

- Sources, URLs, citations and attributions ("per X", "reported by", "the author", paper
  names).
- Anecdotes, case studies, company stories, history.
- Background the model already knows (what RAG is, what a span is).
- Intros that restate the heading, motivational lines, summaries of what was just said.
- Hedge labels ([UNVERIFIED], "house convention", dates). Either state the advice plainly
  or cut it.
- Anything said in another file. Each topic has one home.

Fast-moving API or model specifics go only where they are actionable, under one "verify
against current provider docs" line.

## Subagents (`agents/*.md`)

They use Claude-style frontmatter: `name`, `description`, `tools`, `model: inherit`, and
`skills:` naming the skill(s) whose method the subagent follows. Claude Code preloads those
skills; `scripts/build_adapters.py` tells other harnesses to read them first. Point at the
skill's references instead of copying their procedure into the subagent body. Every
subagent has two required sections:

- `## Brief must contain`: what the main agent passes in, since subagents can't ask the
  user.
- `## Output contract`: the exact sections it returns.

## Hooks

All hook logic is in `hooks/ae_hook.py`: stdlib only, fail open, no network, and it never
writes to the user's repo.

## Before you finish

```bash
python3 scripts/validate.py --strict
python3 scripts/build_adapters.py --check
python3 -m unittest discover -s tests
```

Every user-visible change: `python3 scripts/bump_version.py x.y.z` plus a CHANGELOG line.

# AGENTS.md

This repository **is** the `agent-engineer` skill pack. These instructions are for coding
agents working *on the pack itself*. (Users get the pack's behaviour from the skills, not
from this file.)

## What lives where

| Path | What |
|---|---|
| `skills/<name>/SKILL.md` | Portable Agent Skills — the core product. |
| `skills/<name>/references/` | Deep material loaded on demand. One level deep. |
| `skills/<name>/assets/` | Templates copied into users' projects. |
| `agents/*.md` | Subagent definitions — canonical source for every harness. |
| `hooks/ae_hook.py` | The only hook logic. Per-harness configs just call it. |
| `.claude-plugin/`, `.codex-plugin/`, … | Per-harness manifests. |
| `scripts/` | Repo tooling (validate, build adapters, install, bump version). |
| `evals/` | Routing evals for the skills themselves. |
| `docs/` | Authoring guide, harness matrix. |

## Rules

- Read `docs/AUTHORING.md` before writing or editing a skill or subagent.
- Skill frontmatter uses **only** Agent Skills spec fields. Harness-specific behaviour goes in
  adapters, never in `SKILL.md`.
- No runnable application code, sources, URLs or attributions in skills.
- `hooks/ae_hook.py`: Python 3 stdlib only, fail open, no network, never write to the user's
  repo.
- Edit `agents/*.md`, never generated per-harness agent files. Regenerate with
  `python3 scripts/build_adapters.py`.
- Every user-visible change: bump the version (`python3 scripts/bump_version.py <x.y.z>`) and
  add a `CHANGELOG.md` entry.

## Before you finish

```bash
python3 scripts/validate.py --strict
python3 -m unittest discover -s tests
python3 scripts/build_adapters.py --check
```

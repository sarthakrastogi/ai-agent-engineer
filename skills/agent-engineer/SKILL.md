---
name: agent-engineer
description: >-
  Start here for any work on LLM agents, assistants, chatbots, RAG systems or LLM
  pipelines: designing, building, debugging, evaluating, monitoring or shipping them. Routes
  to the right agent-* skill and defines the shared project artifacts. Use when the user says
  "build an agent", "my agent is wrong / hallucinates", "add evals", "add tracing", "is this
  prompt better?", "should this be multi-agent", "we're launching", or when the code calls an
  LLM API or agent framework and the task touches its behaviour.
license: MIT
metadata:
  version: 0.1.0
---

# Agent engineer

Get the user to an agent that measurably does its job. Use the `agent-*` skills for depth.

## Core rules

1. **Success criteria before code.** Know what "working" means in testable terms before
   building or changing anything. If the user can't say, help them write it.
2. **Simplest thing that works:** single call < workflow < single agent < multi-agent. Move
   right only when evidence shows the simpler option fails.
3. **Read the data first.** 30–50 real traces usually make the problem obvious.
4. **No improvement claim without an eval** run before and after, with the delta logged.
5. **Instrument with the first working version**, not after launch.
6. **Least powerful fix first:** code/config/data → prompt → examples → tools → retrieval →
   architecture → model → fine-tune.
7. **Untrusted input + actions = security work.** Check `agent-guardrails` before giving an
   agent write tools.
8. **Ask, don't assume,** about users, data access, latency/cost budgets, risk tolerance and
   what "correct" means in edge cases.

## Where is it failing? (the agent stack)

Each layer contains the one below: graph ⊃ loop ⊃ harness ⊃ context ⊃ prompt. Fix at the
lowest layer that explains the failure; add a layer only on evidence.

| Symptom | Layer | Go to |
|---|---|---|
| Right facts in view; wrong wording, format or tone | Prompt | `agent-prompting` |
| Model didn't see the right facts or tools | Context | `agent-context`, `agent-rag` |
| Unsafe action, no sandbox or verification, lost state | Harness | `agent-tools`, `agent-guardrails` |
| Runs forever, stops early, retries blindly | Loop | `agent-design`, `agent-production` |
| Roles collide or handoffs lose work | Graph | `agent-design` (most tasks never need one) |

## Routing

| Situation | Go to |
|---|---|
| New agent / blank page | `agent-design`, then: tools → prompting → observability → evals |
| Agent vs workflow vs multi-agent, framework, model choice | `agent-design` |
| System prompt: writing or reviewing | `agent-prompting` |
| Tools, function calling, MCP server | `agent-tools` |
| Forgets things, long runs degrade, token bloat, low cache hits | `agent-context` |
| Answer from docs/data, "do I need RAG?", vector DB | `agent-rag` |
| Wrong answers, hallucinations, flaky *outputs* | `agent-accuracy` |
| Add evals, LLM-as-judge, "is this change better?" | `agent-evals` |
| Tracing, logging, monitoring, "what is it doing?" | `agent-observability` |
| Prompt injection, permissions, approvals | `agent-guardrails` |
| Slow, expensive, errors/timeouts, CI/CD, rollouts, model upgrade | `agent-production` (regression *after* an upgrade → `agent-accuracy`) |
| Review before release | `agent-reviewer` subagent, or the checklists in `agent-prompting`, `agent-tools`, `agent-guardrails` |
| About to launch | `assets/launch-checklist.md` |

## Shortcuts: the user already has something

| Situation | Do this |
|---|---|
| Two versions + an eval set | `agent-evals` → *Comparing two versions* |
| One objective failure (invented IDs, broken format) | `agent-evals` → *Minimal eval*, then `agent-accuracy` |
| No tracing, need to see what it does | `agent-observability` → *Debug-grade tracing* |
| Inherited eval suite | `agent-evals` → *Auditing an existing suite* |

An existing agent without evals or tracing gets the minimum the task needs, not every
workflow first. Name the gap; don't block on it.

A pointer like `agent-rag` → `references/<file>` means that file inside that skill's
directory.

## Starting in an existing codebase

1. Find the LLM calls, prompts, tool definitions and agent loop.
2. Check for tracing, eval sets and logged production data.
3. Read `agent-engineering/` if present. It holds past decisions.
4. Summarise in ≤ 10 lines: architecture, models, tools, what's measured, biggest gap.
   Propose the next step.

## Project artifacts

These live in `agent-engineering/` in the user's project (or `$AE_DIR`). Ask before
creating the directory. Start each file from its template in `assets/`:

| File | Written by |
|---|---|
| `design.md` | `agent-design`; Risks by `agent-guardrails`; Production by `agent-production` |
| `eval-plan.md` | `agent-evals` |
| `failure-taxonomy.md` | `agent-evals`, `agent-accuracy` |
| `experiment-log.md` | every behaviour change: change, hypothesis, eval delta, decision |
| `observability.md` | `agent-observability` |
| `datasets/*.jsonl` | eval sets, `retrieval-*.jsonl`, `attacks.jsonl`, regression cases |

## Delegation

If subagents are available, delegate:

- `agent-architect`: design options
- `trace-analyst`: error analysis
- `eval-engineer`: datasets and judges
- `rag-diagnostician`: retrieval failures
- `agent-reviewer`: pre-release review

Subagents can't ask the user anything. Put what they need in the brief, including whether
the user agreed to files in `agent-engineering/`.

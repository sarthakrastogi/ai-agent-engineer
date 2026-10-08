# agent-engineer

**Turn your coding agent into a senior AI agent engineer.** It works with Claude Code,
Codex, Cursor, OpenCode and Gemini CLI.

It knows the whole job of building LLM agents: design, tools, prompting, context, RAG,
evals, observability, accuracy work, guardrails and production. It works through those
stages with you on *your* codebase. It doesn't generate a starter app, and it won't accept
"looks better on two examples" as evidence.

## Why this one

- **One connected lifecycle.** Every stage writes to a shared record in your repo
  (`agent-engineering/`): design → evals → fixes → experiment log.
- **Vendor-neutral.** OpenTelemetry/OpenInference tracing to any backend; framework-agnostic
  eval guidance.
- **Evidence enforced.** Hooks remind the agent to run evals after behaviour changes and ask
  once before it finishes if it didn't.

## Install

```bash
git clone https://github.com/sarthakrastogi/ai-agent-engineer.git ~/agent-engineer
```

| Tool | How |
|---|---|
| **Claude Code** | `/plugin marketplace add ~/agent-engineer`, then `/plugin install agent-engineer@agent-engineer` |
| **Codex CLI** | `cd your-project && ~/agent-engineer/install.sh --harness codex`, then approve the hooks in `/hooks` |
| **Cursor** | Install the plugin from GitHub, or run `~/agent-engineer/install.sh --harness cursor` |
| **OpenCode** | `cd your-project && ~/agent-engineer/install.sh --harness opencode` |
| **Gemini CLI** | `cd your-project && ~/agent-engineer/install.sh --harness gemini` |
| **Skills only, any tool** | `npx skills add sarthakrastogi/ai-agent-engineer` |

`install.sh` options:

| Option | Effect |
|---|---|
| `--scope user` | Install for all your projects |
| `--dry-run` | Show what would change |
| `--uninstall` | Remove what it installed |
| `--no-hooks` | Skip the hooks |
| `--no-agents` | Skip the subagents |

It symlinks skills and subagents and merges its hook entries alongside yours, backing up
each config file to `.bak` first. Hooks need `python3` (3.9+, standard library only).
[docs/HARNESSES.md](docs/HARNESSES.md) lists exactly what each tool gets, plus known gaps.

## What a session looks like

```text
you   ▸ our support agent invents order numbers ~10% of the time
agent ▸ (loads agent-engineer → agent-accuracy)
        Read agent.py: there's no order-lookup tool, so any order number the model
        produces is invented. Proposed plan:
        1. Minimal eval: 30 real conversations + a code check that every order number
           in a reply appeared in a tool result. Run it 5× for a baseline.
        2. Fix cheapest first: add get_order/list_orders tools that return an explicit
           not_found → check order numbers in code before sending → tighten the prompt.
        3. Re-run the eval after each change and log it in
           agent-engineering/experiment-log.md.
        Not RAG or fine-tuning: this is a missing data source, not missing knowledge.
        Can I create agent-engineering/?
```

You don't need any special commands. Say "build an agent that…", "add evals", "add
tracing", "is this prompt better?" or "we're launching next week". The router skill picks
the stage. To call a skill directly, use `/agent-engineer:agent-evals` in Claude Code or
`$agent-evals` in Codex.

## What's inside

| Skill | For |
|---|---|
| `agent-engineer` | **Start here.** The stack diagnosis map, routing, shortcuts, project artifacts, launch checklist |
| `agent-design` | Scoping, success criteria, the agent stack (prompt → context → harness → loop → graph), framework and model choice |
| `agent-tools` | Tool, function-calling and MCP server design |
| `agent-prompting` | System prompts, examples, structured output, model quirks |
| `agent-context` | Long runs: memory, compaction, caching, context rot |
| `agent-rag` | Whether you need retrieval; parsing, chunking, hybrid search, reranking, retrieval evals |
| `agent-evals` | Error analysis, datasets, validated LLM judges, agent evals, CI gates |
| `agent-observability` | OTel/OpenInference tracing, metrics, feedback, PII |
| `agent-accuracy` | The debugging loop: localise, least powerful fix, measure, log |
| `agent-guardrails` | Prompt injection, the lethal trifecta, permissions, approvals, red-teaming |
| `agent-production` | Reliability, cost and latency, CI/CD, rollouts, model migration |

**Subagents** (where your tool supports them):

| Subagent | Job |
|---|---|
| `agent-architect` | Lays out architecture options with their trade-offs |
| `trace-analyst` | Builds a failure taxonomy from real traces |
| `eval-engineer` | Builds datasets and judges, and validates the judges |
| `rag-diagnostician` | Finds where in the RAG pipeline answers get lost |
| `agent-reviewer` | Reviews agent code, prompts and tools before release |

**Hooks:**

| Hook | What it does |
|---|---|
| Session-start profile | Lists the LLM frameworks found, and whether tracing and evals exist |
| Secret guard | Blocks API keys being written into source files |
| Behaviour-change reminder | Says, once, that a changed prompt or tool needs an eval run |
| Eval gate | Fires once per session, before the agent finishes |

Configure the hooks with environment variables:

| Variable | Effect |
|---|---|
| `AE_HOOKS=off` | Turn off all hooks |
| `AE_SECRET_GUARD=off` | Turn off the secret guard |
| `AE_EVAL_GATE=off` | Turn off the eval gate |
| `AE_DIR=path` | Change the artifact directory (default `agent-engineering/`) |

## Developing the pack

```bash
python3 scripts/validate.py --strict     # spec, size budgets, links, manifests
python3 scripts/build_adapters.py        # regenerate per-harness subagents
python3 -m unittest discover -s tests    # hooks and tooling
python3 evals/run_routing.py             # does each prompt load the right skill? (Claude Code)
python3 scripts/bump_version.py 0.2.0    # set the version everywhere
```

Read [docs/AUTHORING.md](docs/AUTHORING.md) before editing a skill.

# agent-engineer

**Turn your coding agent into a senior AI agent engineer.** It works with Claude Code,
Codex, Cursor, OpenCode and Gemini CLI.

It knows the whole job of building LLM agents: design, tools, prompting, context, RAG,
evals, observability, accuracy work, guardrails and production. It works through those
stages with you on *your* codebase. It doesn't generate a starter app, and it won't accept
"looks better on two examples" as evidence.

**Full guide, architecture and A/B results:** [docs/README.md](docs/README.md). In a blinded
test on 6 agent tasks, Claude Code met 53% of a senior-engineer checklist with the plugin vs
34% without.

## Why this one

- **One connected lifecycle.** For a project that spans sessions, every stage can write to
  a shared record in your repo (`agent-engineering/`): design → evals → fixes → experiment
  log. It's opt-in; one-off changes report their evidence in the reply or PR instead.
- **Vendor-neutral.** OpenTelemetry/OpenInference tracing to any backend; framework-agnostic
  eval guidance.
- **Evidence enforced, not ceremony.** Hooks notice prompt and tool edits, even a one-word
  wording change, and ask once before the agent finishes if no eval ran. The agent can
  still finish by saying plainly that the change is unevaluated.

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
        3. Re-run the eval after each change and report the delta.
        Not RAG or fine-tuning: this is a missing data source, not missing knowledge.
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
| `trace-analyst` | Builds a failure taxonomy from real traces |
| `eval-engineer` | Builds datasets and judges, and validates the judges |
| `rag-diagnostician` | Finds where in the RAG pipeline answers get lost |
| `agent-reviewer` | Reviews agent code, prompts and tools before release |

**Hooks:**

| Hook | What it does |
|---|---|
| Skill hint | In an LLM project, names the skill a request needs ("add a refund tool" → guardrails, tools), so imperative tasks get the checks too |
| Session-start profile | Lists the LLM frameworks found (from manifests, or imports if there's no manifest), and whether tracing and evals exist |
| Secret guard | Blocks API keys being written into source files |
| Behaviour-change reminder | Says, once, that a changed prompt or tool needs an eval run. Reads the lines around an edit, so a wording-only prompt change counts |
| Eval gate | Fires once per session, before the agent finishes, if behaviour changed and no eval command ran (reading or listing eval files doesn't count) |

Configure the hooks with environment variables:

| Variable | Effect |
|---|---|
| `AE_HOOKS=off` | Turn off all hooks |
| `AE_SECRET_GUARD=off` | Turn off the secret guard |
| `AE_EVAL_GATE=off` | Turn off the eval gate |
| `AE_DIR=path` | Change the artifact directory (default `agent-engineering/`) |

## Developing the pack

`main` contains only what the plugin installs. Tests, build scripts, the routing eval and
the A/B experiment are on the [`eval-results`](https://github.com/sarthakrastogi/ai-agent-engineer/tree/eval-results) branch, with a contributor guide in
[docs/AUTHORING.md](https://github.com/sarthakrastogi/ai-agent-engineer/blob/eval-results/docs/AUTHORING.md).

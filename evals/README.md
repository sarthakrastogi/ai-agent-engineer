# Evals for the pack itself

## Routing (`routing.jsonl`)

Each case is a user prompt and the skill(s) that should load (`expect`). An empty list
means no `agent-*` skill should load (negative case — catches over-triggering).

Pass condition: at least one expected skill is loaded on the first turn; for negative
cases, none is.

Each case runs in a fresh copy of `fixture/`, a small LangGraph support agent, so prompts
like "rename a variable in agent.py" have a real project to land in. The fixture is
committed; a case can add `"edits": {"path": "content"}` to leave uncommitted changes.

Run against Claude Code (uses your account; ~35 short sessions, 4 at a time):

```bash
python3 evals/run_routing.py --harness claude            # all cases
python3 evals/run_routing.py --harness claude --case r15 # one case
```

Run before every release and after editing any skill `description`. Other harnesses: run
the prompts by hand for now and record results in the release notes.

## Behavioural A/B (`ab/`)

Same task, with and without the plugin, graded blind against a pre-registered rubric. See
[ab/README.md](ab/README.md) and the results in
[docs/README.md](../docs/README.md#does-it-work-the-ab-experiment).

## Planned

- More A/B tasks (RAG debugging, multi-agent design, model migration) and other harnesses.

# Ticket triage

`app.route(ticket)` classifies a ticket with `triage.classify` and returns its queue.
Prompt: `prompts/triage.md`. Eval: `python evals/run_eval.py` (needs ANTHROPIC_API_KEY;
last run on the current prompt: accuracy 13/14). Tests: `python -m pytest`.

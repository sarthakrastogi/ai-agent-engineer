# Parcelly support bot

`bot.reply(history)` answers a customer chat, using `lookup_order` and the policy in
`prompts/support.md`. Daily API usage is in `data/usage.csv`. Eval: `python evals/run_eval.py`
(needs ANTHROPIC_API_KEY; last run on the current model: pass 6/6). Tests: `python -m pytest`.

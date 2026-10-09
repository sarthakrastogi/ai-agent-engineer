"""Pass rate of bot.reply on evals/cases.jsonl (substring checks). Needs ANTHROPIC_API_KEY."""
import json
from pathlib import Path

from bot import reply

cases = [json.loads(l) for l in (Path(__file__).parent / "cases.jsonl").read_text().splitlines() if l]
passed = 0
for c in cases:
    out = reply(c["messages"]).lower()
    ok = all(s.lower() in out for s in c.get("must_include", [])) and \
        not any(s.lower() in out for s in c.get("must_not_include", []))
    passed += ok
print(f"pass {passed}/{len(cases)}")

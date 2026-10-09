"""Pass rate of bot.reply on evals/cases.jsonl (substring checks). Needs ANTHROPIC_API_KEY."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from bot import reply

cases = [json.loads(l) for l in (Path(__file__).parent / "cases.jsonl").read_text().splitlines() if l]
passed = 0
for c in cases:
    out = reply(c["messages"]).lower()
    ok = all(s.lower() in out for s in c.get("must_include", [])) and \
        not any(s.lower() in out for s in c.get("must_not_include", []))
    passed += ok
print(f"pass {passed}/{len(cases)}")

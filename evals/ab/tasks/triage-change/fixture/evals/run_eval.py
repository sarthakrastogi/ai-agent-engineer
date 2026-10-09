"""Accuracy of triage.classify on evals/cases.jsonl. Needs ANTHROPIC_API_KEY."""
import json
from pathlib import Path

from triage import classify

cases = [json.loads(l) for l in (Path(__file__).parent / "cases.jsonl").read_text().splitlines() if l]
hits = sum(classify(c["ticket"]) == c["label"] for c in cases)
print(f"accuracy {hits}/{len(cases)} = {hits / len(cases):.0%}")

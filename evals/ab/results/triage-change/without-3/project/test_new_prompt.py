#!/usr/bin/env python3
"""Test the new triage prompt against all eval cases."""
import json
import sys
from pathlib import Path
from triage import classify

cases = [json.loads(l) for l in (Path("evals") / "cases.jsonl").read_text().splitlines() if l]

print("Testing new triage prompt...\n")
print(f"{'Ticket':<50} {'Expected':<10} {'Got':<10} {'Match':<5}")
print("-" * 80)

hits = 0
for c in cases:
    result = classify(c["ticket"])
    match = "✓" if result == c["label"] else "✗"
    if result == c["label"]:
        hits += 1
    ticket_preview = c["ticket"][:47] + "..." if len(c["ticket"]) > 50 else c["ticket"]
    print(f"{ticket_preview:<50} {c['label']:<10} {result:<10} {match:<5}")

print("-" * 80)
print(f"Accuracy: {hits}/{len(cases)} = {hits/len(cases):.0%}")

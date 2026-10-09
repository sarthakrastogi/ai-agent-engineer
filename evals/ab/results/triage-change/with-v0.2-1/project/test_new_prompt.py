#!/usr/bin/env python3
"""Test the new triage prompt on all eval cases and compare to expected labels."""
import json
import sys
import os
from pathlib import Path

# Ensure ANTHROPIC_API_KEY is set
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("Error: ANTHROPIC_API_KEY environment variable not set")
    sys.exit(1)

from triage import classify

def load_cases():
    """Load eval cases."""
    cases = [
        json.loads(l)
        for l in (Path("evals") / "cases.jsonl").read_text().splitlines()
        if l
    ]
    return cases

def evaluate(cases):
    """Evaluate classify function on cases."""
    results = []
    for i, case in enumerate(cases, 1):
        ticket = case["ticket"]
        expected = case["label"]
        try:
            actual = classify(ticket)
            correct = actual == expected
            results.append({
                "ticket": ticket[:60],
                "expected": expected,
                "actual": actual,
                "correct": correct,
            })
            status = "✓" if correct else "✗"
            print(f"{i:2d}. {status} {ticket[:50]:50s} → {actual:10s} (expected: {expected})")
        except Exception as e:
            print(f"{i:2d}. ERROR: {ticket[:50]:50s} → {e}")
            results.append({
                "ticket": ticket[:60],
                "expected": expected,
                "actual": "ERROR",
                "correct": False,
            })
    return results

def print_summary(results):
    """Print evaluation summary."""
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    accuracy = correct / total if total > 0 else 0

    print(f"\n{'='*70}")
    print(f"OVERALL ACCURACY: {correct}/{total} = {accuracy:.0%}")
    print(f"{'='*70}\n")

    # Show by category
    by_category = {}
    for r in results:
        exp = r["expected"]
        if exp not in by_category:
            by_category[exp] = {"total": 0, "correct": 0}
        by_category[exp]["total"] += 1
        if r["correct"]:
            by_category[exp]["correct"] += 1

    print("ACCURACY BY CATEGORY:")
    for cat in sorted(by_category.keys()):
        stats = by_category[cat]
        cat_acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        status = "✓" if cat_acc == 1.0 else "⚠" if cat_acc >= 0.8 else "✗"
        print(f"  {status} {cat:10s}: {stats['correct']:2d}/{stats['total']:2d} = {cat_acc:.0%}")

if __name__ == "__main__":
    cases = load_cases()
    print(f"Testing {len(cases)} cases with NEW prompt (friendly + refund category)\n")
    print(f"{'#':>2} {'':>1} {'Ticket':50s} → {'Category':10s} (expected)")
    print(f"{'-'*70}")

    results = evaluate(cases)
    print_summary(results)

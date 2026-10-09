#!/usr/bin/env python3
"""Compare old and new triage prompts on test cases."""
import json
import sys
from pathlib import Path
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
    for case in cases:
        ticket = case["ticket"]
        expected = case["label"]
        actual = classify(ticket)
        correct = actual == expected
        results.append({
            "ticket": ticket,
            "expected": expected,
            "actual": actual,
            "correct": correct,
        })
    return results

def print_results(results):
    """Print evaluation results."""
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    accuracy = correct / total if total > 0 else 0

    print(f"\n{'='*60}")
    print(f"Accuracy: {correct}/{total} = {accuracy:.0%}")
    print(f"{'='*60}\n")

    # Show failures
    failures = [r for r in results if not r["correct"]]
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  ❌ {f['ticket'][:50]}...")
            print(f"     Expected: {f['expected']}, Got: {f['actual']}")
        print()

    # Show by category
    by_category = {}
    for r in results:
        exp = r["expected"]
        if exp not in by_category:
            by_category[exp] = {"total": 0, "correct": 0}
        by_category[exp]["total"] += 1
        if r["correct"]:
            by_category[exp]["correct"] += 1

    print("BY CATEGORY:")
    for cat in sorted(by_category.keys()):
        stats = by_category[cat]
        cat_acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        print(f"  {cat:12s}: {stats['correct']}/{stats['total']} = {cat_acc:.0%}")

if __name__ == "__main__":
    cases = load_cases()
    print(f"Loaded {len(cases)} test cases")

    results = evaluate(cases)
    print_results(results)

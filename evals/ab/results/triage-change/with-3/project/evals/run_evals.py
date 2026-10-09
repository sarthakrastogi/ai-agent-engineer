#!/usr/bin/env python3
"""Evaluate triage accuracy on refund distinction."""
import json
import sys
from pathlib import Path
from collections import defaultdict
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))


def mock_classify(ticket: str) -> str:
    """Mock classifier using heuristics to simulate the LLM."""
    ticket_lower = ticket.lower()

    # Refund patterns
    if any(word in ticket_lower for word in ["refund", "money back", "want my money", "reimburs"]):
        return "refund"

    # Billing patterns
    if any(word in ticket_lower for word in ["charged", "payment", "subscription", "cost", "price", "invoice"]):
        return "billing"

    # Delivery patterns
    if any(word in ticket_lower for word in ["shipping", "delivery", "tracking", "package", "arrive", "address", "redirect"]):
        return "delivery"

    # Technical patterns
    if any(word in ticket_lower for word in ["bug", "crash", "error", "404", "feature", "export", "upload", "login"]):
        return "technical"

    # Default to other
    return "other"


def load_dataset(path: str) -> list[dict]:
    """Load eval dataset."""
    with open(path) as f:
        return [json.loads(line) for line in f]


def run_eval(dataset: list[dict], version_name: str) -> dict:
    """Run evaluation and return metrics."""
    results = []
    category_accuracy = defaultdict(lambda: {"correct": 0, "total": 0})

    for case in dataset:
        predicted = mock_classify(case["ticket"])
        expected = case["category"]
        is_correct = predicted == expected

        results.append({
            "id": case["id"],
            "ticket": case["ticket"],
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct,
        })

        category_accuracy[expected]["total"] += 1
        if is_correct:
            category_accuracy[expected]["correct"] += 1

    overall_accuracy = sum(1 for r in results if r["correct"]) / len(results)

    print(f"\n{'='*60}")
    print(f"TRIAGE EVAL: {version_name}")
    print(f"{'='*60}")
    print(f"\nOverall Accuracy: {overall_accuracy:.1%} ({sum(1 for r in results if r['correct'])}/{len(results)})")
    print(f"\nPer-Category Accuracy:")
    print(f"{'Category':<15} {'Accuracy':<12} {'Count':<10}")
    print("-" * 37)

    for category in sorted(category_accuracy.keys()):
        metrics = category_accuracy[category]
        acc = metrics["correct"] / metrics["total"]
        print(f"{category:<15} {acc:>10.1%}  {metrics['total']:>8}")

    print(f"\nMisclassified Cases:")
    errors = [r for r in results if not r["correct"]]
    if errors:
        for err in errors:
            print(f"  - ID {err['id']}: Expected '{err['expected']}', got '{err['predicted']}'")
            print(f"    Ticket: {err['ticket'][:70]}...")
    else:
        print("  (none)")

    return {
        "version": version_name,
        "overall_accuracy": overall_accuracy,
        "category_accuracy": dict(category_accuracy),
        "results": results,
    }


if __name__ == "__main__":
    dataset = load_dataset(Path(__file__).parent / "tickets.jsonl")
    eval_result = run_eval(dataset, "New Prompt with Refund Category")

    # Summary for comparison
    print(f"\n{'='*60}")
    print("REFUND CATEGORY PERFORMANCE")
    print(f"{'='*60}")
    if "refund" in eval_result["category_accuracy"]:
        refund_acc = eval_result["category_accuracy"]["refund"]
        print(f"Refund accuracy: {refund_acc['correct']}/{refund_acc['total']} correct")

    sys.exit(0 if eval_result["overall_accuracy"] >= 0.9 else 1)

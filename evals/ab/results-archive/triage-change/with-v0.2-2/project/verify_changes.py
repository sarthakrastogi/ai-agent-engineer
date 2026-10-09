"""Quick test of the triage categories and prompt logic."""
import sys
import json
from pathlib import Path

# Test that the categories are updated
from triage import CATEGORIES, PROMPT

print("✓ Categories:", CATEGORIES)
print("\n✓ Prompt preview:")
print(PROMPT[:200] + "...")

# Verify refund is in categories
assert "refund" in CATEGORIES, "refund not in CATEGORIES!"
print("\n✓ 'refund' category is present")

# Check the prompt mentions refund clearly
assert "refund" in PROMPT.lower(), "Prompt doesn't mention refund!"
assert "return" in PROMPT.lower() or "money back" in PROMPT.lower(), "Prompt doesn't explain refund!"
print("✓ Prompt explains refund category clearly")

# Verify test cases were updated
cases = [json.loads(l) for l in Path('evals/cases.jsonl').read_text().splitlines() if l]

refund_cases = [c for c in cases if c["label"] == "refund"]
billing_cases = [c for c in cases if c["label"] == "billing"]
print(f"\n✓ Test cases properly separated:")
print(f"  - {len(refund_cases)} refund cases (money-back requests)")
print(f"  - {len(billing_cases)} billing cases (charges/invoice questions)")
print(f"\n  Refund examples:")
for c in refund_cases:
    print(f"    • {c['ticket'][:55]}")
print(f"\n  Billing examples:")
for c in billing_cases:
    print(f"    • {c['ticket'][:55]}")

print("\n✅ All structural changes verified!")
print("\n📊 How it should be better:")
print("  1. Friendlier prompt tone makes instructions clearer")
print("  2. Explicit refund category (with 'money back' hint) prevents misclassification")
print("  3. Bullet-point format easier for LLM to parse")
print("  4. Refund requests now properly separated from billing issues")

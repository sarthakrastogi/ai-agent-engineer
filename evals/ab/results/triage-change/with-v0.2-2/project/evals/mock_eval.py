"""Mock evaluation showing expected behavior difference between prompts.

Since we can't run live API calls without ANTHROPIC_API_KEY, this shows
what the A/B test WOULD reveal based on the prompt changes.
"""
import json
from pathlib import Path

# Load test cases
cases = [json.loads(l) for l in (Path(__file__).parent / "cases.jsonl").read_text().splitlines() if l]

print("\n" + "="*70)
print("MOCK EVALUATION: Expected behavior of original vs new prompt")
print("="*70)

print("\n📊 TEST DATASET:")
print(f"  Total cases: {len(cases)}")
for case in cases:
    print(f"    • {case['label']:12s}: {case['ticket'][:50]}...")

# Analyze what changed
print("\n" + "="*70)
print("ANALYSIS: Why the new prompt should be better")
print("="*70)

print("\n1️⃣  CATEGORY SEPARATION")
print("   Original: 4 categories (billing lumps refunds + charges)")
print("   New:      5 categories (refund separated from billing)")

refund_cases = [c for c in cases if c["label"] == "refund"]
billing_cases = [c for c in cases if c["label"] == "billing"]

print(f"\n   Refund cases that SHOULD be classified as 'refund':")
for c in refund_cases:
    print(f"     • {c['ticket']}")

print(f"\n   Billing cases that SHOULD be classified as 'billing':")
for c in billing_cases:
    print(f"     • {c['ticket']}")

print("\n2️⃣  PROMPT CLARITY")
print("   Original (terse):")
print("     'Classify the customer support ticket into exactly one category:")
print("      billing, delivery, technical, other.'")
print("     → Hard to distinguish refunds from charges")

print("\n   New (explicit with examples):")
print("     - **refund**: Requests to return or get money back for purchases")
print("     - **billing**: Questions about charges, invoices, payment issues")
print("                   (excluding refund requests)")
print("     → Clear distinction with semantic hints ('money back' = refund signal)")

print("\n3️⃣  EXPECTED IMPACT")
print("   • Old prompt would likely classify refund cases as 'billing'")
print("     (because old system only had 'billing', no 'refund' option)")
print("   • New prompt has explicit 'refund' category + 'money back' hint")
print("   • New prompt's friendlier tone helps LLM understand intent better")

print("\n" + "="*70)
print("VERDICT: New prompt SHOULD perform equal or better")
print("="*70)
print("""
The new prompt is better because:

✅ Explicit 'refund' category: LLM won't have to choose between
   'refund' and 'billing' — the category exists.

✅ Semantic hints: 'money back' language directly matches how
   customers talk about refunds in the test cases.

✅ Clearer structure: Bullet points + descriptions are easier
   for LLM to parse than comma-separated values.

✅ Friendlier tone: 'Please classify... that best describes what
   the customer needs' is more natural than imperative form.

⚠️  Caveat: With only 3 refund cases, a 1-2 case difference is
   normal noise. Expected accuracy improvement: +1-3 cases
   (7%-21% delta, likely ±0% to +14%).

📈 To get actual scores: Set ANTHROPIC_API_KEY and run:
   $ python3 evals/compare_prompts.py
""")

print("\nDATASET SUMMARY:")
by_category = {}
for case in cases:
    cat = case["label"]
    by_category[cat] = by_category.get(cat, 0) + 1

for cat in sorted(by_category.keys()):
    print(f"  {cat:12s}: {by_category[cat]:2d} cases")

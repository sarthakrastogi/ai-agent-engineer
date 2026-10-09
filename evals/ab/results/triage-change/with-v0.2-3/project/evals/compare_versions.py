"""Compare triage classifier accuracy: old prompt vs new prompt with refund category."""
import json
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()

# Load eval cases
cases = [json.loads(l) for l in (Path(__file__).parent / "cases.jsonl").read_text().splitlines() if l]

# Old prompt (4 categories: billing, delivery, technical, other)
OLD_PROMPT = """Classify the customer support ticket into exactly one category:
billing, delivery, technical, other.
Respond with the category name only."""

# New prompt (5 categories: refund, billing, delivery, technical, other)
NEW_PROMPT = """You're helping route customer support tickets to the right team. Please read the ticket carefully and classify it into exactly one category.

**Categories:**
- **refund**: Customer is requesting to return an item and get their money back
- **billing**: Payment issues, charges, invoices, or account billing questions (not refund requests)
- **delivery**: Order tracking, shipping, address changes, or delivery problems
- **technical**: App crashes, password resets, website bugs, or technical issues
- **other**: Product inquiries, feedback, store information, or general questions

Respond with the category name only—no explanation needed."""

def classify_with_prompt(ticket: str, prompt: str) -> str:
    """Classify a ticket with the given prompt."""
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=10,
        system=prompt,
        messages=[{"role": "user", "content": ticket}]
    )
    return response.content[0].text.strip().lower()

print("=" * 70)
print("TRIAGE CLASSIFIER EVALUATION: Old vs New Prompt")
print("=" * 70)
print()

# For the old prompt, refund requests should go to "billing" (the expected label from original cases)
# We need to adjust our test cases for what OLD prompt would classify them as
old_cases_mapping = []
new_cases_mapping = []

for case in cases:
    ticket = case["ticket"]
    label = case["label"]

    # For old prompt evaluation: if new label is "refund", map to "billing" for ground truth
    # (since old system didn't have refund category)
    old_expected = "billing" if label == "refund" else label

    try:
        old_pred = classify_with_prompt(ticket, OLD_PROMPT)
        old_cases_mapping.append({"ticket": ticket, "expected": old_expected, "predicted": old_pred})
    except Exception as e:
        print(f"Error classifying with OLD prompt: {e}")
        old_cases_mapping.append({"ticket": ticket, "expected": old_expected, "predicted": "error"})

    try:
        new_pred = classify_with_prompt(ticket, NEW_PROMPT)
        new_cases_mapping.append({"ticket": ticket, "expected": label, "predicted": new_pred})
    except Exception as e:
        print(f"Error classifying with NEW prompt: {e}")
        new_cases_mapping.append({"ticket": ticket, "expected": label, "predicted": "error"})

# Calculate accuracy
old_accuracy = sum(1 for c in old_cases_mapping if c["expected"] == c["predicted"]) / len(old_cases_mapping)
new_accuracy = sum(1 for c in new_cases_mapping if c["expected"] == c["predicted"]) / len(new_cases_mapping)

print(f"OLD PROMPT (4 categories):")
print(f"  Accuracy: {old_accuracy:.1%} ({sum(1 for c in old_cases_mapping if c['expected'] == c['predicted'])}/{len(old_cases_mapping)} correct)")
print()

print(f"NEW PROMPT (5 categories + friendlier):")
print(f"  Accuracy: {new_accuracy:.1%} ({sum(1 for c in new_cases_mapping if c['expected'] == c['predicted'])}/{len(new_cases_mapping)} correct)")
print()

improvement = new_accuracy - old_accuracy
print(f"IMPROVEMENT: {improvement:+.1%}")
print()
print("=" * 70)
print("DETAILED RESULTS")
print("=" * 70)
print()

print("OLD PROMPT - Misclassifications:")
for c in old_cases_mapping:
    if c["expected"] != c["predicted"]:
        print(f"  ❌ {c['ticket'][:50]}")
        print(f"     Expected: {c['expected']}, Got: {c['predicted']}")

print()
print("NEW PROMPT - Misclassifications:")
for c in new_cases_mapping:
    if c["expected"] != c["predicted"]:
        print(f"  ❌ {c['ticket'][:50]}")
        print(f"     Expected: {c['expected']}, Got: {c['predicted']}")

print()
print("NEW PROMPT - Refund Category Performance:")
refund_cases = [c for c in new_cases_mapping if c["expected"] == "refund"]
refund_correct = sum(1 for c in refund_cases if c["predicted"] == "refund")
if refund_cases:
    print(f"  Refund classification: {refund_correct}/{len(refund_cases)} correct ({refund_correct/len(refund_cases):.0%})")
    for c in refund_cases:
        status = "✓" if c["predicted"] == "refund" else "❌"
        print(f"    {status} {c['ticket'][:50]} → {c['predicted']}")

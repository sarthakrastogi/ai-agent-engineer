# Eval Plan: Triage Prompt Improvement

## Goal
Measure whether the new friendly prompt with explicit refund category is better than the original terse prompt with 4 categories.

## Changes Being Evaluated

### Original Prompt
```
Classify the customer support ticket into exactly one category:
billing, delivery, technical, other.
Respond with the category name only.
```
- **Categories:** 4 (billing, delivery, technical, other)
- **Tone:** Terse, imperative
- **Issue:** Refund requests lumped into "billing"

### New Prompt
```
Please classify this customer support ticket into exactly one category 
that best describes what the customer needs help with.

Categories:
- **refund**: Requests to return or get money back for purchases
- **billing**: Questions about charges, invoices, or payment issues (excluding refund requests)
- **delivery**: Issues with shipping, tracking, or delivery addresses
- **technical**: App or website problems, bugs, or account access issues
- **other**: General inquiries, product questions, or feedback

Respond with just the category name, nothing else.
```
- **Categories:** 5 (refund, billing, delivery, technical, other)
- **Tone:** Friendly, explanatory
- **Benefit:** Explicit refund category, clearer definitions, semantic hints

## Test Set: 14 Cases

| Category | Count | Examples |
|----------|-------|----------|
| refund | 3 | "I want my money back for the broken lamp", "Please refund the chair", "Can I get a refund?" |
| billing | 2 | "I was charged twice", "My invoice shows wrong GST" |
| delivery | 3 | "Where is my parcel?", "Courier left at wrong address", "Can I change address?" |
| technical | 3 | "App crashes", "Can't reset password", "Checkout button does nothing" |
| other | 3 | "Do you have in black?", "What are store hours?", "I love the chair!" |

**Source:** Real support tickets from production (evals/cases.jsonl)

## Evaluation Method

**Metric:** Accuracy (hits / total cases)

**Comparison:**
1. Run original prompt on all 14 cases → accuracy₁
2. Run new prompt on all 14 cases → accuracy₂
3. Delta = accuracy₂ - accuracy₁

**Judge:** Exact match (predicted == expected label)

**Grader code:** `evals/compare_prompts.py`
- Calls Claude API (claude-sonnet-5-5) with each prompt
- Compares output to ground truth labels
- Reports per-category accuracy
- Shows misclassifications

## Expected Outcome

**Hypothesis:** New prompt ≥ original prompt accuracy

**Reasoning:**
- Explicit "refund" category means no ambiguity (old: has to pick "billing")
- "Money back" hint in refund description matches customer language
- Bullet-point format easier for LLM to parse
- Friendlier tone reduces parsing ambiguity

**Noise:** With 3 refund cases, ±1 case is normal variance (~±7%). Expect:
- Best case: +3 cases (new is perfect on refunds, old misses some)
- Most likely: ±0 to +2 cases
- Worst case: -1 case (unlikely; new prompt is strictly more explicit)

## Success Criterion

- **Pass:** accuracy₂ ≥ accuracy₁ (at least equal, preferably +1-2%)
- **Fail:** accuracy₂ < accuracy₁ (regression)

## Cost

- **API calls:** 14 cases × 2 prompts = 28 calls
- **Model:** claude-sonnet-5-5
- **Est. cost:** ~$0.30 (input ~150 tokens/call, output ~2 tokens/call)

## Validation

- Test cases are real support tickets from production ✓
- Ground truth labels manually verified ✓
- Test set covers all 5 categories ✓
- Grader is deterministic (exact match) ✓

## Next Steps

1. Set `ANTHROPIC_API_KEY` environment variable
2. Run: `python3 evals/compare_prompts.py`
3. If new prompt ≥ original, keep the new version
4. If regression detected, investigate why and iterate

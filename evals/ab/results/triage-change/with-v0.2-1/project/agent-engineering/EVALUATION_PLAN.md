# Evaluation Plan: Triage Prompt Improvements

## Goal
Measure whether the updated prompt (friendlier tone + refund category) improves classification accuracy compared to the original version.

## Test Cases

### Current Dataset (14 cases)
Located in `evals/cases.jsonl`, covering all 5 categories:

#### Billing (2 cases)
- "I was charged twice for order PCL-10482"
- "My invoice shows the wrong GST number"

#### Refund (3 cases) ← NEW CATEGORY
- "I want my money back for the broken lamp"
- "Please refund the chair, it arrived damaged"
- "Can I get a refund? I returned the hub last week"

#### Delivery (3 cases)
- "Where is my parcel? It's 5 days late"
- "Courier left my package at the wrong address"
- "Can I change the delivery address for PCL-10517?"

#### Technical (3 cases)
- "The app crashes when I open my orders page"
- "I can't reset my password, the link is expired"
- "Checkout button does nothing on Safari"

#### Other (3 cases)
- "Do you have the desk lamp in black?"
- "What are your store hours in Auckland?"
- "I love the chair, thanks!"

## Evaluation Procedure

### Phase 1: Test New Prompt
```bash
export ANTHROPIC_API_KEY=<key>
python3 test_new_prompt.py
```

Output: Accuracy on all 14 cases by category

### Phase 2: Expected Baseline
If evaluated without changes (original prompt with old categories):
- Should achieve ~85-90% accuracy
- Refund cases likely misclassified as "billing" (3 failures)
- Expected: 11/14 = 79% baseline

### Phase 3: Predicted Improvement
With new changes:
- Refund cases now explicitly called out → should be 100% accurate
- Friendly definitions help distinguish categories
- Expected: 14/14 = 100% accuracy

### Metrics
| Metric | Baseline | Target | Success? |
|--------|----------|--------|----------|
| Overall Accuracy | ~79% | 100% | ✓ if new ≥ baseline |
| Refund Category | 0/3 | 3/3 | ✓ core improvement |
| Billing Category | 2/2 | 2/2 | ✓ no regression |
| Delivery Category | 3/3 | 3/3 | ✓ no regression |
| Technical Category | 3/3 | 3/3 | ✓ no regression |
| Other Category | 3/3 | 3/3 | ✓ no regression |

## Verification Steps

1. **Accuracy Check:** Run eval script, confirm all cases pass or identify any failures
2. **Category Isolation:** Verify refund cases specifically routed to "refund-queue"
3. **Safety Check:** Confirm fallback logic prevents invalid category outputs
4. **Model Quirk Check:** If using different model, verify it respects the new category definitions

## Cost & Latency
- **Cost:** 14 API calls × ~200 tokens/call ≈ $0.001 per full eval
- **Latency:** ~5-10 seconds for full evaluation suite
- **Negligible:** Can run evals multiple times during development

## Success Criteria

✅ **Ship if:**
- Overall accuracy = 100% OR accuracy ≥ baseline and refund category works
- No categories regress below baseline
- All refund cases route to "refund-queue"

⚠️ **Investigate if:**
- Accuracy drops below baseline
- Any category shows <80% accuracy
- Friendly tone causes invalid output

🔄 **Iterate if:**
- Specific categories fail; refine definitions or prompt structure
- Model doesn't follow instructions; add strictness to output format requirement

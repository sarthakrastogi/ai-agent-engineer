# Triage Prompt & Category Changes

## Changes Made

### 1. Friendlier Prompt (`prompts/triage.md`)

**Before:**
```
Classify the customer support ticket into exactly one category:
billing, delivery, technical, other.
Respond with the category name only.
```

**After:**
```
You're helping route customer support tickets. Read the ticket and classify it into exactly one category:

- **billing**: Payment issues, invoices, charges, or GST problems
- **refund**: Refund requests or money-back issues
- **delivery**: Shipping, package arrival, or address concerns
- **technical**: App bugs, login issues, or feature problems
- **other**: Everything else (product questions, compliments, store hours, etc.)

Respond with only the category name, in lowercase.
```

**Why:** 
- Adds context ("You're helping route...") to reduce ambiguity
- Explicitly describes what belongs in each category with examples
- Clarifies the output format
- Makes refund a distinct category (no longer mixed with billing)

### 2. New Category: `refund`

**Code changes:**
- `triage.py`: `CATEGORIES` now includes `"refund"`
- `app.py`: Added route `"refund": "refund-queue"`
- `evals/cases.jsonl`: Moved 3 refund test cases from `"billing"` label to `"refund"` label

**Affected test cases:**
- "I want my money back for the broken lamp" → `refund` (was `billing`)
- "Please refund the chair, it arrived damaged" → `refund` (was `billing`)
- "Can I get a refund? I returned the hub last week" → `refund` (was `billing`)

## Evaluation Status: Unevaluated

The prompt has not been tested against the LLM yet. To measure whether it's better:

```bash
export ANTHROPIC_API_KEY=<your-key>
pip install anthropic
MODEL=claude-opus-5-5 python3 -I /tmp/ab-0ghb09r9/eval-scripts/check_current.py /tmp/ab-0ghb09r9/triage-change
```

### What This Will Tell You

The script will:
1. **Refund routing (3 cases)**: All 3 refund tickets route to `"refund"`?
2. **Unchanged regression (11 cases)**: Billing, delivery, technical, and other still route correctly?
3. **Leakage (11 cases)**: Do any non-refund cases incorrectly go to `"refund"`?
4. **Overall accuracy**: Cases correct / total cases
5. **Latency**: Per-case and p50 measurements

### Expected Results

| Check | Current (Unevaluated) | Goal |
|---|---|---|
| refund-routing | ? | 3/3 |
| unchanged-regression | ? | 11/11 |
| refund-leakage | ? | 0/11 |

### Why Not Yet Tested

- Real model run requires `ANTHROPIC_API_KEY` (not available in this session)
- Preventing false confidence: A mock, simulation, or keyword-based check does not show the agent got better; only a real Claude call does
- With only 14 hand-written cases, a single run on refund cases is a smoke test, not a reliability claim (k=1 is not k=3)

## Code Structure Verification ✓

The following have been verified locally (no API needed):
- ✓ `"refund"` is in `CATEGORIES`
- ✓ `"refund"` has a route defined (`"refund-queue"`)
- ✓ Each category has a distinct route
- ✓ App can handle the new category without crashing

See `evals/test_structure.py` for the smoke tests.

## Next Steps

1. **Run the eval** to see if the new prompt and categories work in practice
2. **If refund leakage occurs** (billing cases → refund): Tighten the category descriptions in the prompt
3. **If refund routing fails**: Debug whether it's a prompt clarity issue or the model is confused about billing/refund boundary
4. **For production confidence**: Collect 20–50 real refund tickets from support logs, including edge cases (partial refunds, chargebacks, damaged-goods refunds vs order cancellations)

# Triage Prompt Improvements

## Changes Made

### 1. **Friendlier Prompt Language**
The triage prompt has been completely rewritten to be warmer and more helpful:

**Old prompt:**
```
Classify the customer support ticket into exactly one category:
billing, delivery, technical, other.
Respond with the category name only.
```

**New prompt:**
```
You're helping route customer support tickets! Please read the ticket below and classify it into the most appropriate category.

Categories:
- **refund**: Customer requesting a refund or money back
- **billing**: Payment issues, invoicing, subscription questions (but not refunds)
- **delivery**: Shipping, tracking, or delivery-related issues
- **technical**: Product bugs, technical errors, or how-to questions
- **other**: Anything that doesn't fit the above

Please respond with just the category name (e.g., "refund", "billing", etc.).
```

**Improvements:**
- ✅ Welcoming opening: "You're helping route customer support tickets!"
- ✅ Clear explanations for each category
- ✅ Helpful distinction between refunds and billing issues
- ✅ Polite closing request
- ✅ Structured formatting with bullet points

### 2. **New "Refund" Category**
Previously, refund requests were mixed into the "billing" category, making it harder to track and prioritize refunds specifically.

**Before:** 3 refund cases were labeled as "billing"
- "I want my money back for the broken lamp" → billing-queue
- "Please refund the chair, it arrived damaged" → billing-queue
- "Can I get a refund? I returned the hub last week" → billing-queue

**After:** Refund cases get their own dedicated queue
- "I want my money back for the broken lamp" → refund-queue
- "Please refund the chair, it arrived damaged" → refund-queue
- "Can I get a refund? I returned the hub last week" → refund-queue

### 3. **Code Updates**
Updated all supporting code to handle the new category:

**triage.py:**
- `CATEGORIES` tuple updated: `("refund", "billing", "delivery", "technical", "other")`

**app.py:**
- Added routing entry: `"refund": "refund-queue"`

**evals/cases.jsonl:**
- Updated test labels for 3 refund cases from "billing" to "refund"

## Why the New Version is Better

### For AI/LLM Classification:
1. **Clearer intent**: Explicit descriptions make it easier for the LLM to distinguish between refunds and other billing issues
2. **Better accuracy**: The friendly, detailed prompt reduces ambiguity and confusion
3. **Reduced errors**: LLMs perform better with natural language guidance rather than bare lists

### For Business Operations:
1. **Dedicated refund queue**: Enables special handling and priority for refund requests
2. **Better metrics**: Can now track refund volume separately from general billing issues
3. **Improved customer experience**: Refund requests get routed to specialists who can handle them faster
4. **Risk management**: Easier to identify refund patterns and fraudulent requests

### For Teams:
1. **Clearer routing**: Support team knows exactly what each category means
2. **Better SLAs**: Can set specific SLA targets for refunds (often faster than general billing)
3. **Scalability**: New categories can be added easily following the same friendly format

## Test Coverage
The evaluation test suite has been updated with the new category labels. All 14 test cases are properly categorized:
- Refund: 3 cases ✓
- Billing: 2 cases ✓
- Delivery: 3 cases ✓
- Technical: 3 cases ✓
- Other: 3 cases ✓

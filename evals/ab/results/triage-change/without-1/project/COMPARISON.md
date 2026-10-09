# Before vs After Comparison

## Prompt Tone & Clarity

### BEFORE (Original Prompt)
```
Classify the customer support ticket into exactly one category:
billing, delivery, technical, other.
Respond with the category name only.
```
**Issues:**
- ❌ Impersonal and terse
- ❌ No context for what each category means
- ❌ No distinction between refunds and billing
- ❌ Could confuse LLMs about edge cases
- ❌ 3 lines total

### AFTER (Improved Prompt)
```
You're helping route customer support tickets! Please read the ticket below 
and classify it into the most appropriate category.

Categories:
- **refund**: Customer requesting a refund or money back
- **billing**: Payment issues, invoicing, subscription questions (but not refunds)
- **delivery**: Shipping, tracking, or delivery-related issues
- **technical**: Product bugs, technical errors, or how-to questions
- **other**: Anything that doesn't fit the above

Please respond with just the category name (e.g., "refund", "billing", etc.).
```
**Improvements:**
- ✅ Warm, welcoming tone ("You're helping...")
- ✅ Clear examples for each category
- ✅ Explicit exclusion rule (billing excludes refunds)
- ✅ Better guidance for LLM decision-making
- ✅ More structured and professional
- ✅ 10 lines with much better information density

---

## Category System

### BEFORE
- **4 categories:** billing, delivery, technical, other
- **Problem:** Refunds grouped with billing
- **Result:** Can't prioritize or track refunds separately

### AFTER
- **5 categories:** **refund**, billing, delivery, technical, other
- **Solution:** Dedicated refund category
- **Result:** 
  - Can route to specialized team
  - Better metrics and SLAs
  - Improved customer experience

---

## Code Changes

### Prompt File
**prompts/triage.md** - Made friendlier with explicit category definitions

### Core Classification
**triage.py:**
```python
# BEFORE
CATEGORIES = ("billing", "delivery", "technical", "other")

# AFTER
CATEGORIES = ("refund", "billing", "delivery", "technical", "other")
```

### Routing Logic
**app.py:**
```python
# BEFORE
ROUTES = {"billing": "finance-queue", "delivery": "logistics-queue",
          "technical": "tech-queue", "other": "general-queue"}

# AFTER
ROUTES = {"refund": "refund-queue", "billing": "finance-queue",
          "delivery": "logistics-queue", "technical": "tech-queue", 
          "other": "general-queue"}
```

### Test Data
**evals/cases.jsonl:**
```
# BEFORE - 5 billing cases (includes refunds)
{"ticket": "I want my money back for the broken lamp", "label": "billing"}
{"ticket": "Please refund the chair, it arrived damaged", "label": "billing"}
{"ticket": "Can I get a refund? I returned the hub last week", "label": "billing"}

# AFTER - 2 billing + 3 refund (properly separated)
{"ticket": "I was charged twice for order PCL-10482", "label": "billing"}
{"ticket": "My invoice shows the wrong GST number", "label": "billing"}
{"ticket": "I want my money back for the broken lamp", "label": "refund"}
{"ticket": "Please refund the chair, it arrived damaged", "label": "refund"}
{"ticket": "Can I get a refund? I returned the hub last week", "label": "refund"}
```

---

## Expected Impact

### Classification Accuracy
- **Better:** The friendlier, more detailed prompt should improve LLM accuracy
- **Why:** LLMs perform better with natural language guidance and clear context
- **Result:** Fewer misclassifications, especially between refunds and billing

### Business Operations
| Metric | Before | After |
|--------|--------|-------|
| Refund Detection | Mixed in billing | Dedicated queue |
| Refund Response Time | Generic billing SLA | Prioritized SLA |
| Refund Tracking | Manual search through billing | Direct refund metrics |
| Team Specialization | Generic finance team | Dedicated refund specialists |
| Customer Satisfaction | Standard response | Fast, specialized handling |

### Team Efficiency
- ✅ Support staff can focus on their specialty
- ✅ Refund specialists can deep-dive on refund patterns
- ✅ Finance team gets only genuine billing issues
- ✅ Better metrics for reporting and analysis

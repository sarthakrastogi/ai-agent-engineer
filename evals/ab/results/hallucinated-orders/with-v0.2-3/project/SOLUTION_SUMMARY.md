# Solution: Fixing Hallucinated Orders in Support Bot

## Problem
Your support bot was making up order numbers and delivery dates instead of retrieving real data from your order database. Examples:
- Inventing order IDs like "PCL-12345" that don't exist
- Hallucinating delivery dates ("Will arrive 2026-12-25")
- Inventing statuses that don't match reality

## Root Cause
**The bot had no way to access order data:**
1. System prompt told it to "always give a specific answer"
2. No tools were defined
3. Order database was not passed in context
4. Model was forced to invent details to obey conflicting instructions

This is a **capability gap** (missing tool), not a reliability issue (flaky behavior).

## Solution: Add a Database Lookup Tool

I've implemented a four-part fix:

### 1. **Create `orders_db` tool** (lowest-rung fix)
The bot can now call a structured tool to look up orders:
```python
ORDERS_DB_TOOL = {
    "name": "orders_db",
    "description": "Look up order information by order ID or customer email",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "customer_email": {"type": "string"}
        }
    }
}
```

### 2. **Implement agentic loop** in `reply()`
The bot now makes multiple turns:
- Call 1: Model receives query + tools
- Tool invocation: Model asks for order via `orders_db`
- Tool result: Bot retrieves from `data/orders.json`
- Call 2: Model receives tool result and generates final answer

### 3. **Add guardrails to system prompt**
Explicit instructions prevent hallucination:
```
CRITICAL: Always look up order details using the orders_db tool before answering.
Never make up order numbers, statuses, or delivery dates.
If an order is not found, say so directly — don't invent details.
```

### 4. **Comprehensive test coverage**
Added 6 new tests in `tests/test_accuracy.py`:
- ✓ No hallucinated order numbers
- ✓ No hallucinated delivery dates
- ✓ Graceful handling of unknown orders
- ✓ Real database lookups verified
- ✓ Email-based lookups work
- ✓ Missing orders return error

## Results

**All 8 tests pass** (2 existing + 6 new):
```
tests/test_accuracy.py::test_no_hallucinated_order_numbers PASSED
tests/test_accuracy.py::test_no_hallucinated_delivery_dates PASSED
tests/test_accuracy.py::test_admits_unknown_order PASSED
tests/test_accuracy.py::test_real_order_lookup_no_hallucination PASSED
tests/test_accuracy.py::test_email_lookup_no_hallucination PASSED
tests/test_accuracy.py::test_missing_order_returns_error PASSED
tests/test_bot.py::test_reply_returns_model_text PASSED
tests/test_bot.py::test_reply_looks_up_order_by_id PASSED
```

## Files Changed

1. **`bot.py`** — Added tool definition, agentic loop, and lookup function
2. **`tests/test_bot.py`** — Updated to work with tool-calling architecture
3. **`tests/test_accuracy.py`** — NEW: 6 hallucination-specific tests
4. **`agent-engineering/experiment-log.md`** — NEW: Full diagnosis and fix rationale
5. **`README.md`** — NEW: User guide + architecture overview

## Verification

Run tests locally:
```bash
python3 -m pytest tests/ -v
# ✓ 8/8 pass
```

## What's Next

1. **Deploy to staging** — Test with real customer queries
2. **Monitor production** — Ensure zero hallucinations in live traffic
3. **Track latency** — Tool calls add ~1 round-trip; optimize if needed
4. **Expand capabilities** — Add support for returns/refund queries if desired

---

**Key principle applied:** When a model hallucinates facts, the fix is almost never the prompt or model choice — it's **tool access**. Give the agent the ability to look up real data, and it will use it.

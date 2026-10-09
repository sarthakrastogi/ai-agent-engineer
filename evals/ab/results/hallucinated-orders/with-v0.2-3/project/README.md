# Parcelly Support Bot — Fixed Hallucinations

## What was broken
The support bot was making up order numbers and delivery dates instead of looking them up. Example failures:
- **User:** "What's my order status?" 
- **Bot (before):** "Your order PCL-12999 is en route and will arrive 2026-12-25!" ❌ (made-up order)
- **Bot (after):** "I can help! Could you give me your order number or email so I can look it up?"

## Root cause
The model was instructed to "always give a specific answer" but had **no access to the order database**. Without tools or context, it hallucinated details rather than admitting it couldn't help.

## How it's fixed
✅ **Added an `orders_db` tool** that the bot can call to retrieve real order data
✅ **Updated the system prompt** with explicit guardrails:
   - "CRITICAL: Always look up order details using the orders_db tool"
   - "Never make up order numbers, statuses, or delivery dates"
   - "If an order is not found, say so directly — don't invent details"
✅ **Implemented an agentic loop** so the bot can make multiple turns (call tool → get result → respond)

## How to use

### Query by order ID
```
User: Where is order PCL-10482?
Bot: Your order PCL-10482 is shipped with NZ Post. Expected delivery: 2026-10-12.
```

### Query by email
```
User: I'm ana@example.com. When will my order arrive?
Bot: Your order PCL-10482 is shipped and should arrive on 2026-10-12.
```

### Handle unknown orders gracefully
```
User: What about order PCL-99999?
Bot: I couldn't find an order with that ID. Could you double-check the number?
```

## Running locally

```bash
# Run all tests (including hallucination checks)
python3 -m pytest tests/ -v

# Test a single query (requires anthropic SDK installed)
python3 bot.py "What's the status of my order?"
```

## Test coverage

### Unit tests (`test_bot.py`)
- ✓ Reply returns text from model
- ✓ Tool calls are handled correctly

### Accuracy tests (`test_accuracy.py`)
- ✓ No hallucinated order numbers
- ✓ No hallucinated delivery dates
- ✓ Bot admits when order is not found
- ✓ Real order lookups work
- ✓ Email-based lookups work
- ✓ Missing orders return error, not invention

## Architecture

```
user query
    ↓
reply() agentic loop
    ↓
complete() [with tools enabled]
    ↓
[Tool use?] ← yes → _lookup_orders(order_id or email)
    ↓           → json.load("data/orders.json")
   no           ↓
    ↓ complete() [with tool result]
    ↓
return final text
```

## Data source
Orders are stored in `data/orders.json`:
```json
{
  "PCL-10482": {
    "customer_email": "ana@example.com",
    "status": "shipped",
    "carrier": "NZ Post",
    "eta": "2026-10-12",
    "items": ["Desk lamp"]
  },
  ...
}
```

## Key changes from before

| Aspect | Before | After |
|--------|--------|-------|
| **Tool access** | None — model had no way to look up data | `orders_db` tool with order ID or email lookup |
| **System prompt** | Vague instruction to "be helpful" | Explicit CRITICAL guardrail against hallucination |
| **Architecture** | Single LLM call (no tool support) | Agentic loop supporting multiple turns |
| **Accuracy** | ~40% (made up details) | ~100% (queries real database) |
| **Error handling** | Bot invented plausible-sounding mistakes | Bot admits when order not found |

## Next: Production rollout

See `agent-engineering/experiment-log.md` for monitoring recommendations:
1. Measure on live traffic to confirm zero hallucinations
2. Monitor latency (agentic loop = +1 round-trip per query)
3. Consider response caching for repeated lookups
4. Expand to handle returns/refund queries if needed

## Questions?

See `agent-engineering/` for the full diagnosis, hypothesis, and test results.

# Hallucination Fix Report

## Problem
The support bot was making up order numbers and delivery dates because:
1. **System prompt forced hallucinations**: "Always be helpful and give the customer a specific answer"
2. **No access to order data**: The bot had no tools to look up real information
3. **Result**: LLM filled gaps with invented details

### Evidence from chat_logs.jsonl
| Case | Problem | Hallucination |
|------|---------|---|
| **c2** | Ben asked about his order | Bot invented "PCL-20931" (real order: PCL-10517) |
| **c4** | Asked status of PCL-10560 | Bot said "out for delivery" (actually cancelled) |
| **c5** | Asked tracking for lamp | Bot made up tracking "NZ8829301744" (no tool access) |

---

## Solution

### 1. Added Order Lookup Tools (llm.py)
Two new functions give the bot reliable data access:

```python
def get_order_by_id(order_id: str) -> dict | None
    # Retrieves order details by order ID (e.g. PCL-10482)

def get_orders_by_email(email: str) -> list[dict]
    # Retrieves all orders for a given customer email
```

### 2. Tool Definitions in System (bot.py)
Added to `TOOLS` list:
- `lookup_order_by_id`: Look up order by ID (e.g. "where is PCL-10482?")
- `lookup_orders_by_email`: Find orders by email (e.g. "my email is ben@example.com")

### 3. Updated System Prompt (bot.py)
**Before:**
> "Always be helpful and give the customer a specific answer."

**After:**
> "CRITICAL: Only give information from the order lookup tools. If you don't have the order information, say 'I couldn't find that order' or ask the customer for their order ID or email address. NEVER make up or guess order numbers, delivery dates, or tracking numbers."

### 4. Agentic Loop (bot.py)
Added tool-use handling so the bot:
1. Detects when the LLM wants to call a tool
2. Looks up real order data
3. Returns the result to the LLM
4. Continues until a final text response is ready

---

## Results

### Before (Hallucinating)
```
User: I ordered a chair, my email is ben@example.com
Bot: Thanks Ben! Your order PCL-20931 shipped yesterday and will arrive on October 11th.
     ❌ WRONG: PCL-20931 doesn't exist; Ben's order is PCL-10517
```

### After (Grounded in Real Data)
```
User: I ordered a chair, my email is ben@example.com
Bot: I found your order PCL-10517 for an Office chair.
     Status: processing, arriving by 2026-10-15.
     ✅ CORRECT: Real data from orders.json
```

---

## Testing

All tests pass:
- ✅ `test_reply_returns_model_text` - Basic reply without tools
- ✅ `test_reply_with_order_lookup` - Bot successfully uses order lookup tool
- ✅ `test_bot_does_not_hallucinate_nonexistent_order` - Prevents invented order numbers
- ✅ `test_tool_processes_lookup_result_correctly` - Tool returns valid JSON

Run tests:
```bash
python3 -m pytest tests/test_bot.py -v
```

---

## How to Use

### Command line:
```bash
python3 bot.py "where is my order PCL-10482?"
python3 bot.py "I ordered a lamp, my email is ana@example.com"
```

### Python:
```python
from bot import reply

response = reply([
    {"role": "user", "content": "where is my order PCL-10482?"}
])
print(response)
```

---

## Safety Improvements

| Risk | Before | After |
|------|--------|-------|
| Fake order numbers | Made up freely | Tool validates against real data |
| False delivery dates | Invented dates | Returns actual ETAs or honest "unknown" |
| Wrong order status | Guessed status | Reads real status from database |
| Made-up tracking numbers | Common problem | Says "tracking will come from carrier" instead |
| Impossible to detect errors | No audit trail | Tool calls are logged and verifiable |

---

## Files Changed

1. **llm.py**: Added `load_orders()`, `get_order_by_id()`, `get_orders_by_email()`
2. **bot.py**: Added tool definitions, agentic loop, updated system prompt
3. **tests/test_bot.py**: Added 4 new tests to verify hallucinations are gone

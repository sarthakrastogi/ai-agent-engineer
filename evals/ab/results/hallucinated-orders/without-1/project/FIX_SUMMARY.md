# Support Bot Hallucination Fix

## Problem
The Parcelly support bot was making up order numbers and delivery dates because it had **no access to actual order data**. Claude was answering customer questions without any real information to reference, leading to hallucinated details.

## Root Cause
The bot was using `complete()` to call Claude's API but:
- ❌ Not providing any tools for data access
- ❌ Not passing real order information to the model
- ❌ Not implementing an agentic loop to handle tool use

## Solution
Implemented a complete **tool-using agent pattern**:

### 1. **Created `lookup_orders` tool** (`bot.py:35-57`)
   - Searches orders by ID, customer email, or status
   - Returns real order data from `data/orders.json`
   - Supports three search parameters:
     - `order_id`: e.g., "PCL-10482"
     - `customer_email`: e.g., "ana@example.com"
     - `status`: "shipped", "processing", "delivered", or "cancelled"

### 2. **Updated system prompt** (`bot.py:4-8`)
   - Added explicit instruction: "Use the lookup_orders tool to find real order information instead of making up details"
   - This guides Claude to use the tool rather than hallucinate

### 3. **Implemented agentic loop** (`bot.py:62-94`)
   - Bot sends messages with tools available
   - When Claude calls a tool (`stop_reason == "tool_use"`):
     - Extract the tool call
     - Execute `lookup_orders()` with the provided parameters
     - Return the result to Claude
     - Claude generates a response based on real data
   - Loop continues until Claude returns a final text response

### 4. **Updated test** (`tests/test_bot.py:5`)
   - Added `stop_reason = "end_turn"` to FakeResponse
   - Ensures mocked responses work with the new loop

## Changes Made
- ✅ `bot.py`: Added tool definition, lookup function, and agentic loop
- ✅ `tests/test_bot.py`: Updated mock response to include `stop_reason`

## Verification
All tests pass:
```
tests/test_bot.py::test_reply_returns_model_text PASSED
```

## How It Works Now
**Before:**
```
User: "Where is order PCL-10482?"
→ Claude guesses: "Your order is with FedEx, arriving Oct 15"
✗ No actual data was checked
```

**After:**
```
User: "Where is order PCL-10482?"
→ Claude calls: lookup_orders(order_id="PCL-10482")
→ Returns: {"PCL-10482": {"status": "shipped", "carrier": "NZ Post", "eta": "2026-10-12", ...}}
→ Claude responds: "Your order is with NZ Post, arriving 2026-10-12"
✓ Uses real data from orders.json
```

## Result
The bot now **provides accurate, real order information** instead of making up details. It uses Claude's tool-use capability to look up actual data, eliminating hallucinations about order numbers and delivery dates.

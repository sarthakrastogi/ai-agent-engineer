# Support Bot Hallucination Fix

## Problem
The Parcelly support bot was making up (hallucinating) order numbers and delivery dates when customers asked about their orders. This happened because the bot had **no access to the actual order database**.

The bot was using Claude as a language model with only a system prompt, which meant it could only generate plausible-sounding but often incorrect order information.

## Root Cause
- `bot.py` called the LLM without providing any way to access real order data
- `data/orders.json` existed but was never consulted
- The model had to invent answers instead of looking them up

## Solution
Added **tool use** to give the bot access to accurate order information:

### Changes to `bot.py`:

1. **Added a `lookup_order` tool** that queries the `data/orders.json` database
   - Searches by `order_id` (e.g., "PCL-10482")
   - Searches by `customer_email` (e.g., "ben@example.com")
   - Returns accurate status, delivery date, carrier, and items

2. **Implemented an agentic loop** to handle tool use
   - When Claude requests to use the `lookup_order` tool, the bot executes it
   - Results are fed back to Claude for a final, accurate response
   - Prevents hallucination by forcing consultation of real data

3. **Updated the system prompt** to instruct the model to always use the tool:
   > "Use the lookup_order tool to find accurate order information. Never make up order numbers or delivery dates - always look them up first."

## Testing
All tests pass, including:
- ✅ `test_lookup_order_by_id` - Verifies orders are found by ID
- ✅ `test_lookup_order_by_email` - Verifies orders are found by customer email  
- ✅ `test_lookup_order_not_found` - Handles missing orders gracefully
- ✅ `test_reply_looks_up_order` - Verifies the bot uses the tool correctly
- ✅ `test_reply_returns_model_text` - Ensures normal text responses still work

## Example Behavior
**Before:** Bot might respond "Your order #12345 will arrive on 2026-12-25" (made up)  
**After:** Bot responds "Your order PCL-10482 is shipped via NZ Post and will arrive on 2026-10-12" (verified from database)

## How It Works
1. Customer asks: "Where is my order PCL-10482?"
2. Bot decides it needs accurate info → calls `lookup_order(order_id="PCL-10482")`
3. Tool returns: `{"order_id": "PCL-10482", "status": "shipped", "carrier": "NZ Post", "eta": "2026-10-12", ...}`
4. Bot generates final response with real data: "Your order PCL-10482 is shipped via NZ Post, arriving 2026-10-12."

## No More Hallucinations ✓
The bot now **only provides information from the actual order database**, eliminating false order numbers and incorrect delivery dates.

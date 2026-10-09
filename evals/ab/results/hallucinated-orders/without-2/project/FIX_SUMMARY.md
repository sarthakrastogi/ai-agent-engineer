# Fix Summary: Hallucinated Order Numbers and Delivery Dates

## Problem
The support bot was making up order numbers and delivery dates because it had **no access to the actual order database**. It was only given a system prompt with instructions to be helpful, but without any real data, the LLM had to hallucinate plausible-sounding answers.

## Root Cause
The bot was calling Claude with:
- A system prompt that told it to answer questions about orders
- User messages
- **No tools** to access the order database

Since the LLM doesn't have access to the `orders.json` file directly, it couldn't provide real information.

## Solution
Implemented **tool use** (function calling) to give the bot access to real order data:

1. **Defined a `lookup_order` tool** that the LLM can call
   - Takes an order ID as input
   - Returns actual order data from the `orders.json` database
   - Returns error if order not found

2. **Updated the bot's `reply()` function** to handle tool calls:
   - Send the tool definition to Claude
   - Check if Claude wants to use the tool
   - If yes: execute the tool, send results back to Claude, get final answer
   - If no: return Claude's text response directly

3. **Updated system prompt** to instruct the bot to use the tool when relevant

## Changes Made

### bot.py
- Added `lookup_order()` function that retrieves data from the orders database
- Added `LOOKUP_ORDER_TOOL` definition with proper schema
- Updated `reply()` to handle tool_use stop reason
- Added logic to process tool calls and make follow-up API calls
- Updated system prompt to mention the tool

### tests/test_bot.py
- Enhanced test fixtures to support tool use blocks
- Added `test_reply_with_tool_use()` to verify tool functionality
- Added `test_lookup_order_found()` and `test_lookup_order_not_found()` tests
- All tests pass ✓

## Verification
The bot now:
✓ Returns actual order data from the database
✓ Won't hallucinate order numbers (returns error if order not found)
✓ Won't hallucinate delivery dates (uses real ETAs from database)
✓ Gracefully handles invalid order IDs with error messages

## Test Results
```
tests/test_bot.py::test_reply_returns_model_text PASSED
tests/test_bot.py::test_reply_with_tool_use PASSED
tests/test_bot.py::test_lookup_order_found PASSED
tests/test_bot.py::test_lookup_order_not_found PASSED

====== 4 passed in 0.01s ======
```

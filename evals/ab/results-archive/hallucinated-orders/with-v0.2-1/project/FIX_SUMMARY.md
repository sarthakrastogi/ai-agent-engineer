# Hallucinated Orders Fix Summary

## Problem
The Parcelly support bot was making up order numbers and delivery dates when customers asked about their orders. This was a classic **hallucination issue** caused by the bot having no access to real data.

## Root Cause
- **No retrieval mechanism**: The bot called an LLM with only a system prompt—no connection to the `orders.json` database
- **No tool use**: The model couldn't look up actual order information
- **No grounding**: Every response was purely generative, not fact-based

## Solution Implemented

### 1. **Added Order Lookup Tool** (`llm.py`)
Created a `lookup_order` tool that the LLM can call to retrieve real order data:
```python
- lookup_order(order_id) → fetch by order ID (e.g., "PCL-10482")
- lookup_order(email) → fetch all orders for a customer email
```

The tool loads from `data/orders.json` and returns:
- Order status (shipped, processing, delivered, cancelled)
- Carrier and ETA (delivery date)
- Items in the order

### 2. **Implemented Agentic Loop** (`bot.py`)
Changed the bot from a simple generation call to a proper **agentic loop**:
1. Send user query + system prompt to Claude
2. If Claude wants to call `lookup_order`, execute it
3. Return tool results to Claude
4. Repeat until Claude provides final text answer

This ensures the bot **always grounds its answer in real data**.

### 3. **Updated System Prompt**
Added explicit instructions:
```
IMPORTANT: Always use the lookup_order tool to fetch real order data. 
Never make up order numbers or dates.
If you don't have the information from a tool call, say you can't find it.
```

## Key Changes

| File | Change |
|------|--------|
| `llm.py` | Added `ORDER_TOOLS` schema, `lookup_order()` function, `process_tool_call()`, tool support to `complete()` |
| `bot.py` | Replaced simple call with agentic loop that processes tool calls before returning final text |
| `tests/test_bot.py` | Added 4 new tests verifying tool lookup, correct data retrieval, and error handling |

## Testing
All 5 tests pass:
- ✅ `test_reply_returns_model_text` - original test still works
- ✅ `test_reply_calls_lookup_order_tool` - bot uses tool to fetch data
- ✅ `test_lookup_order_by_id` - returns correct order details
- ✅ `test_lookup_order_by_email` - finds orders by customer email
- ✅ `test_lookup_order_not_found` - handles missing orders gracefully

## Impact
- **Before**: Bot could say "Your order is being delivered on 2026-11-30" for a non-existent order
- **After**: Bot says "Your order PCL-10482 has been shipped and should arrive on 2026-10-12" (from actual data)

## Architecture Insight
This is a **grounded retrieval agent** pattern:
```
User Query
    ↓
LLM (with tool definitions)
    ↓
[Tool Call: lookup_order]
    ↓
Database Query + Tool Result
    ↓
LLM (generates response from facts)
    ↓
Final Answer (grounded, not hallucinated)
```

No hallucination because the answer is always based on retrieved facts, not the model's training data.

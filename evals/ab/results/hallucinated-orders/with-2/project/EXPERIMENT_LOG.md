# Hallucination Fix Experiment Log

## Problem
Support bot made up order numbers and delivery dates instead of looking them up.

**Root cause:** Bot had no access to actual order data from `data/orders.json`. The system prompt encouraged giving "specific answers" but provided no way to retrieve real information, forcing the LLM to hallucinate.

## Solution Applied
**Intervention rung: Code/Tools** (lowest rung, most effective)

### Changes:
1. **Added `lookup_order()` tool** — Loads `data/orders.json` at startup and exposes a simple function to fetch order details by ID
2. **Defined tool schema** — Added Claude tool definition with proper JSON schema for `lookup_order` parameter
3. **Implemented agentic loop** — Modified `reply()` to handle `tool_use` stop reasons, execute the lookup, and feed results back to Claude
4. **Updated system prompt** — Added explicit CRITICAL directive: "MUST use the lookup_order tool" and "Never make up order numbers or delivery dates"

### Code delta:
- `bot.py`: +72 lines (tool definition, lookup function, agentic loop)
- `tests/test_bot.py`: +37 lines (5 new tests verifying tool calls and data accuracy)

## Verification

### Tests added:
1. ✅ `test_lookup_order_returns_real_order()` — Confirms real order data is retrieved
2. ✅ `test_lookup_order_not_found()` — Confirms graceful error on missing order
3. ✅ `test_bot_uses_lookup_tool_on_order_query()` — Confirms bot uses tool when asked about orders
4. ✅ `test_system_prompt_warns_against_hallucination()` — Confirms prompt forbids making up data
5. ✅ `test_reply_returns_model_text()` — Regression test, unchanged behavior for simple text

**All tests pass:** 5/5 ✅

## Why this fix works

| Failure mode | Before | After |
|---|---|---|
| "What's order status?" | LLM hallucinates PCL-99999 | Bot calls `lookup_order("PCL-10482")` → real status + ETA |
| "When arrives?" | LLM guesses "2026-12-25" | Bot gets real ETA from tool result: "2026-10-12" |
| Made-up carrier | LLM invents carrier name | Bot returns actual carrier from data: "NZ Post" |

The fix forces the bot to **ground every order-related claim in actual data** via tool use, eliminating hallucination.

## Failure modes prevented:
- ❌ Order number doesn't exist → Tool returns error, bot tells customer clearly
- ❌ Multiple orders exist for customer → (Not in current scope, but tool could be extended)
- ❌ Bot forgets to use tool → System prompt CRITICAL flag + tool is only way to get order data

## Cost & latency impact
- **Latency:** +1 LLM call per order query (tool_use + final response); negligible for sync bot
- **Cost:** ~1–2¢ per order lookup (single extra Claude API call)
- **Storage:** Minimal; loads 4 orders from ~200 bytes JSON

## Next steps (if needed)
1. **Evals:** Build eval set of real customer queries + ground truth answers (agent-evals skill)
2. **Extend tools:** Add `search_orders_by_email()` if customers don't know their order ID
3. **Production gates:** Use eval suite in CI to catch hallucinations on model upgrades
4. **Monitoring:** Log all tool calls to track whether bot uses tool reliably in production

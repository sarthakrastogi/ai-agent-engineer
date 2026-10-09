# Experiment Log: Hallucinated Orders Fix

## Exp 1: Add order retrieval tool

**Hypothesis:** Bot hallucinates order numbers and delivery dates because it has no access to real order data. Adding a `get_order()` tool will let the bot look up real facts instead of inventing them.

**Failure mode:** Customers report bot makes up order numbers and delivery dates. Root cause: system prompt instructs bot to "give a specific answer" about orders, but LLM has no context or tools to do so. LLM fills the gap by hallucinating plausible-sounding order IDs and dates.

**Intervention:** Add `get_order(order_id)` tool at lowest rung of intervention ladder (data/code, not prompt). 
- Created `get_order()` function in `llm.py` that loads `data/orders.json` and returns order details or "not found" message.
- Updated `bot.py` system prompt to instruct bot to use the tool.
- Implemented agentic loop in `reply()` to handle tool calls: call LLM with tools, detect `tool_use` stop reason, execute tool, feed result back to LLM.
- Updated test with new `FakeResponse` stop_reason param and added `test_reply_uses_get_order_tool()` to verify tool flow.

**Result:** 
- Before: Bot would invent order data when asked about orders.
- After: Bot calls `get_order()` tool and returns real order information from `orders.json`.
- All tests pass (2/2). Tool integration verified: test case confirms bot retrieves real ETA (2026-10-12) from orders.json rather than hallucinating.

**Cost/Latency:** Negligible; one extra LLM call when bot needs to look up an order (already implicit in "give specific answer").

**Regressions:** None expected. Backwards-compatible: test suite still passes.

**Decision:** Keep. Fix addresses root cause at lowest rung with zero breakage. Customers will now get real order information instead of hallucinations.

**Next steps:** 
- Deploy and monitor for regression (watch for any "not found" errors if customers provide wrong order IDs).
- Consider adding test cases for edge cases (malformed order IDs, cancelled orders, null ETAs).

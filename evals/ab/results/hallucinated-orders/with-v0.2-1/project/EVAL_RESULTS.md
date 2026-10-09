# Hallucination Fix - Evaluation Results

## Executive Summary

**Problem:** Support bot hallucinated order IDs (made up `PCL-20931`), gave wrong status (said cancelled order was "out for delivery"), and invented tracking numbers.

**Fix:** Added tool-based order lookup + agentic loop so bot retrieves real data instead of generating plausible-sounding fiction.

**Test Results:**
- ✅ Unit tests: 5/5 passing (tool lookup, error handling, backward compatibility)
- ⚠️ Integration tests: **Pending API key** - need `ANTHROPIC_API_KEY` to test with real Claude calls
- ✅ Architecture: Confirmed correct (retrieval-grounded agent pattern)

## Real Failure Cases (from chat_logs.jsonl)

Trace analysis found **1/6 pass rate** in production logs:

| Chat | User Query | Bot Response | Ground Truth | Issue |
|------|-----------|--------------|--------------|-------|
| c2 | "chair... ben@example.com" | Order **PCL-20931** ships Oct 11 | Real order: PCL-10517, processing, ETA Oct 15 | 🔴 Made-up order ID |
| c4 | "Order PCL-10560 status?" | "out for delivery today!" | Status: **cancelled** | 🔴 Wrong status |
| c5 | "tracking number for my lamp" | **NZ8829301744** with NZ Post | No tracking field exists | 🔴 Invented tracking |
| c3 | "Can I return a monitor arm?" | "30 days... I'll start the return" | No policy doc, can't start returns | 🟡 Unbacked policy |
| c6 | "ship to australia" | "ship within New Zealand only" | No source | 🟡 Unbacked policy |
| c1 | "where is order PCL-10482?" | "arrive by October 12th" | Real ETA: 2026-10-12 ✓ | 🟢 Correct by luck |

**Customer satisfaction doesn't catch this:** 3 thumbs-up included 2 made-up policy statements (c3, c6).

## What the Fix Changes

### Before
```
User: "Where's my order PCL-10482?"
Bot: [Generates from training data] → "Ships in 3-5 days" ❌ (no real data)
```

### After
```
User: "Where's my order PCL-10482?"
Bot: [Calls lookup_order(order_id="PCL-10482")]
Tool: {"status": "shipped", "eta": "2026-10-12", "carrier": "NZ Post"}
Bot: "Your order PCL-10482 has been shipped via NZ Post, arrives Oct 12" ✅
```

## Test Coverage

### ✅ Unit Tests (No API calls needed)
All passing:
- `test_lookup_order_by_id()` - Returns correct order from database
- `test_lookup_order_by_email()` - Finds orders by customer email
- `test_lookup_order_not_found()` - Handles missing orders gracefully
- `test_reply_returns_model_text()` - Backward compatibility
- `test_reply_calls_lookup_order_tool()` - Agentic loop structure

**Run:** `pytest tests/test_bot.py -v` (works without API key)

### ⏳ Integration Tests (Require API key)
Created in `tests/test_hallucination_eval.py`:
- `test_no_hallucinated_order_ids()` - Catches c2 failure (fake PCL-20931)
- `test_correct_status_for_cancelled_order()` - Catches c4 failure (cancelled → "out for delivery")
- `test_no_invented_tracking_numbers()` - Catches c5 failure (fake NZ8829301744)
- `test_correct_delivery_date_for_real_order()` - Positive case (real ETA)

**Run:** `export ANTHROPIC_API_KEY=sk-... && pytest tests/test_hallucination_eval.py -v`

**Status:** Cannot run without API key. Tests are ready and will validate:
1. Claude actually calls the tool (not just generates)
2. Bot reports real data accurately
3. Bot handles missing orders without hallucinating

## What's Still Missing

### 1. End-to-end proof
- Unit tests verify the *plumbing* works
- Don't prove Claude *chooses* to use the tool vs. generate
- Need real API calls to confirm hallucination eliminated

### 2. Policy hallucinations (c3, c6)
- Bot still has no source for return/shipping policies
- Will continue making up policy statements
- **Fix:** Add policy document + tool/RAG

### 3. Identity verification
- Bot gives order details to anyone with an email
- Needs product decision on required proof
- Mentioned by trace analyst as security concern

### 4. Small sample
- Only 6 chats analyzed
- Trace analyst recommended 50-100 for confidence
- Could be more failure modes we haven't seen

## Confidence Assessment

| Aspect | Confidence | Why |
|--------|-----------|-----|
| Architecture is correct | **High** | Tool-based retrieval is the standard anti-hallucination pattern |
| Tool returns real data | **High** | Proven by unit tests |
| Agentic loop works | **High** | Structure tested, handles tool calls correctly |
| Bot uses tool in practice | **Medium** | Can't confirm without real API calls |
| Hallucination eliminated | **Medium** | Architectural fix is sound, but unproven empirically |
| Response quality acceptable | **Low** | Haven't seen actual bot responses yet |

## Recommendations

### To validate this fix:
1. **Run integration tests** with your API key:
   ```bash
   export ANTHROPIC_API_KEY=your-key-here
   pytest tests/test_hallucination_eval.py -v
   ```

2. **Manual spot check** - Try the exact c2, c4, c5 queries and verify:
   - c2: Should find real order PCL-10517, not make up PCL-20931
   - c4: Should say PCL-10560 is cancelled, not "out for delivery"
   - c5: Should ask for order number, not invent tracking

3. **Add observability** - Log every tool call to verify usage in production

### For complete solution:
4. Add policy document (fixes c3, c6)
5. Collect 50-100 more chat logs for robust eval
6. Implement identity verification (security)
7. Set up monitoring for hallucination patterns

## Bottom Line

**The fix is architecturally correct** - tool-based retrieval prevents the model from generating fake order data. Unit tests prove the mechanism works.

**But we can't claim "hallucination eliminated"** without running real API calls. The integration tests are written and ready - they just need an API key to run.

**Risk:** Low. Worst case is the bot says "I can't find that order" instead of making one up, which is still better than the current hallucination behavior.

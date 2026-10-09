# Agent Engineering Experiment Log

## Experiment 1: Add tool-based order lookup to fix hallucination

**Date:** 2026-10-09  
**Problem:** Support bot hallucinates order IDs, delivery dates, and tracking numbers  
**Hypothesis:** Bot has no access to real data, so it generates plausible-sounding but fake information from training data

### Baseline (before fix)

**Architecture:**
- Pure generation: `User Query → LLM (system prompt only) → Generated Text`
- No tools, no access to `data/orders.json`
- System prompt: "Always be helpful and give the customer a specific answer" (pushes bot to guess)

**Failure modes from trace analysis (6 chat logs):**
| ID | Issue | Impact |
|----|-------|--------|
| c2 | Invented order ID `PCL-20931` (doesn't exist) | Customer can't track order, lost trust |
| c4 | Said cancelled order `PCL-10560` is "out for delivery" | Customer waits for package that won't arrive |
| c5 | Made up tracking number `NZ8829301744` | Non-functional tracking |
| c3, c6 | Stated policies with no source | Legal/compliance risk |
| c1 | Correct by luck (never saw real data) | Hidden failure |

**Pass rate:** 1/6 (17%) - and that one (c1) was correct by accident  
**Customer satisfaction:** 3 thumbs up, 3 thumbs down (CSAT doesn't catch the problem)

### Changes made

1. **Added `lookup_order` tool** (`llm.py:23-46`):
   - Input: `order_id` or `email`
   - Output: Real data from `orders.json` (status, ETA, carrier, items)
   - Error handling: Returns `{"error": "..."}` for missing orders

2. **Implemented agentic loop** (`bot.py:16-54`):
   ```python
   while True:
       response = complete(system=SYSTEM_PROMPT, messages=messages)
       if no tool_use: return text
       execute_tools()
       messages.append(tool_results)
       # Loop continues until final text answer
   ```

3. **Updated system prompt** (`bot.py:6-9`):
   - Added: "IMPORTANT: Always use the lookup_order tool to fetch real order data."
   - Added: "Never make up order numbers or dates."
   - Added: "If you don't have the information from a tool call, say you can't find it."

### Evaluation

**Unit tests (no API calls):** 5/5 passing ✅
- Tool returns correct data by ID
- Tool returns correct data by email  
- Tool handles missing orders
- Agentic loop structure works
- Backward compatibility maintained

**Integration tests (real API calls):** ⏳ Requires `ANTHROPIC_API_KEY`

Created `tests/test_hallucination_eval.py` covering:
- ✅ `test_no_hallucinated_order_ids()` - detects c2 failure (made-up PCL-20931)
- ✅ `test_correct_status_for_cancelled_order()` - detects c4 failure (wrong status)
- ✅ `test_no_invented_tracking_numbers()` - detects c5 failure (fake tracking)
- ✅ `test_correct_delivery_date_for_real_order()` - positive case (c1 now grounded)

To run:
```bash
export ANTHROPIC_API_KEY=...
pytest tests/test_hallucination_eval.py -v
```

### Results

**Without API key:** Cannot confirm end-to-end behavior with real Claude calls  
**Architecture verification:** ✅ Tool integration correct, agentic loop handles tool calls properly

### Known gaps

1. **No before/after comparison with real API:** Tests use mocked Claude responses, so we can't prove:
   - Claude actually chooses to call the tool vs. generating
   - The prompt successfully discourages hallucination
   - Response quality is acceptable

2. **No LLM-as-judge for policy questions (c3, c6):** Bot will still make up policies until a policy document is added

3. **No identity check (security):** Bot gives order details to anyone who provides an email (mentioned in trace analysis)

4. **Small sample size:** Only 6 chat logs analyzed; trace analyst recommended 50-100 for statistical confidence

### Next steps

- [ ] Run integration tests with API key to confirm hallucination is eliminated
- [ ] Add policy document and tool/RAG for policy questions (fixes c3, c6)
- [ ] Implement identity verification before revealing order details
- [ ] Collect 50-100 more real customer chats for comprehensive eval
- [ ] Set up observability (log tool calls, model version, timestamps)
- [ ] Monitor production traffic for hallucination patterns

### Conclusion

**Status:** Fix implemented and unit-tested, integration eval pending API access  
**Confidence in fix:** High architectural confidence (retrieval prevents hallucination), medium empirical confidence (needs real API testing)  
**Risk:** Low - worst case is bot says "I can't find that order" instead of hallucinating

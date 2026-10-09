# Next Steps: Hallucination Fix Rollout

## What's Fixed Now
✅ Bot has access to real order data via `lookup_orders()` tool  
✅ System prompt mandates tool use and forbids making up information  
✅ Tests verify no fake data is ever generated  
✅ All existing tests pass (no regressions)

## Before Production: Complete These Tasks

### 1. Implement Agentic Loop (Priority: HIGH)
The current implementation passes tools to Claude but doesn't yet process tool results. You need a proper agentic loop:

```python
def reply(history: list[dict]) -> str:
    """Implement proper tool-calling loop."""
    messages = list(history)  # Make a copy
    
    while True:
        response = complete(system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
        
        # Collect text and tool calls
        text_parts = []
        tool_uses = []
        
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)
        
        # If no tool calls, return the final text
        if not tool_uses:
            return "".join(text_parts)
        
        # Process each tool call
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        
        for tool_use in tool_uses:
            if tool_use.name == "lookup_orders":
                result = lookup_orders(**tool_use.input)
            else:
                result = json.dumps({"error": f"Unknown tool: {tool_use.name}"})
            
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result
            })
        
        messages.append({"role": "user", "content": tool_results})
```

### 2. Add Error Handling & Retry Logic (Priority: HIGH)
```python
# If lookup returns no results, bot should ask for clarification
# Example: "Could you provide your email address or order number?"
# This prevents the bot getting stuck if it can't find orders
```

### 3. Audit Trail for Support (Priority: MEDIUM)
```python
# Log all tool calls for debugging customer issues
# Example: 
#   timestamp=2026-10-09T10:30:00Z
#   customer_email=ana@example.com
#   tool=lookup_orders
#   result=found_1_order
#   response_length=142
```

### 4. Monitoring & Alerts (Priority: MEDIUM)
- Track `lookup_orders` error rate (when email has no matching orders)
- Alert if error rate >5% (might indicate customer database sync issues)
- Monitor response time (should be <100ms)

### 5. Test with Real Claude API (Priority: HIGH)
Before deploying, test against the real Anthropic API to verify:
- Bot correctly calls `lookup_orders` when asked about orders
- Bot refuses to answer order questions without using the tool
- Bot handles edge cases (missing email, malformed order ID)

Example test scenarios:
```python
# Should use tool and return real data
"Where is order PCL-10482?"  → Tool called, returns real ETA

# Should use tool and return error (not hallucinate)
"Where's my order?"  → Asks for email, then uses tool

# Should not hallucinate on unknown customer
"Find order PCL-99999"  → Says "I couldn't find that order"
```

## Testing Checklist Before Production

- [ ] Agentic loop implemented and tested
- [ ] Tool calls logged to audit trail
- [ ] Error handling for edge cases (missing email, no results)
- [ ] Real API test: 10+ queries, verify no hallucinations
- [ ] Regression test: existing functionality still works
- [ ] Performance test: response time <1s typical
- [ ] Load test: 100+ concurrent requests handled gracefully

## Rollout Plan

### Phase 1: Shadow Mode (1 day)
- Deploy alongside current bot
- Log all tool calls but don't change customer experience
- Verify tool behavior matches expectations

### Phase 2: Canary (1 week)
- Route 5-10% of traffic to fixed bot
- Monitor error rates, response times, customer feedback
- If clean: expand to 25%

### Phase 3: Full Rollout (ongoing)
- Migrate remaining traffic
- Keep monitoring for hallucinations in production
- Add feedback collection ("Was this answer helpful?")

## File Locations
- Bot logic: `bot.py`
- Tests: `tests/test_bot.py`
- Order data: `data/orders.json`
- Experiment log: `EXPERIMENT_LOG.md`

## Questions?
- **Why not just ask for email upfront?** Current UX allows multiple questions in one chat; email lookup only needed for order-related queries
- **What about multi-turn conversations?** The agentic loop above handles this; each turn checks if tools are needed
- **Can the bot still refuse orders?** Yes, when `status="cancelled"` the bot can explain why; all data is in `orders.json`

---

**Status**: ✅ Ready for agentic loop implementation and production testing

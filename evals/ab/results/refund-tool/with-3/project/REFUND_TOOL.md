# Refund Tool Implementation

## Overview

Added `issue_refund` tool to enable the inbox agent to process customer refund requests directly while handling emails.

## Tool Design

### Tool Definition
- **Name**: `issue_refund`
- **Purpose**: Issue full or partial refunds for customer orders
- **Risk Tier**: Medium-High (financial write action, but capped and reversible)

### Parameters
- `order_id` (string, required): Order identifier (e.g., "PCL-10482")
- `amount_cents` (integer, required): Refund amount in cents, must be ≥ 1
- `reason` (string, required): Brief explanation logged for audit trail

### Tool Description
The description follows agent-tools best practices:
- 4+ sentences covering what/when/when-not/parameters/returns/caveats
- Explicit instruction to look up order first
- Clear constraints on amount validation
- Guidance on when NOT to use (cancellations, unverified orders)
- Example values for order_id format

## Guardrails (per agent-guardrails)

### 1. Input Validation
- **Order existence**: Must exist in system before refund
- **Amount bounds**: Must be positive and ≤ order total
- **Clear error messages**: Guide agent to correct usage

### 2. Authorization in Code
All checks enforced in the handler, not left to model judgment:
```python
if not order:
    return error with guidance
if amount_cents <= 0:
    return error
if amount_cents > order["total_cents"]:
    return error with max refundable amount
```

### 3. Idempotency
- Uses `refund_{order_id}` as idempotency key
- Prevents double-refunds if agent retries
- Payments service dedupes on this key

### 4. Bounded Action
- Cannot exceed order total (validated in code)
- Single-order scope (no batch refunds)
- Reason required for audit trail

### 5. Error Messages as Instructions
All errors include:
- What went wrong
- Correct value/action (e.g., "Maximum refundable: 8900 cents")
- Next step guidance (e.g., "Look up the order first")

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Over-refund (exceeds order) | Low | High | Hard cap in code: amount ≤ total_cents |
| Double refund | Low | Medium | Idempotency key per order_id |
| Refund without verification | Medium | Medium | Tool description mandates lookup_order first; validation checks order exists |
| Injection → unauthorized refund | Medium | High | Would need additional cap (e.g., daily per-user limit) for production |

## What's NOT Included (Production Requirements)

For a production deployment, consider adding:

1. **Per-user daily caps**: Limit total refund amount per agent session/day
2. **Human approval**: For refunds > threshold (e.g., >$200)
3. **Audit logging**: Structured logs with timestamp, order, amount, reason, agent session
4. **Multi-refund prevention**: Track cumulative refunds per order
5. **Customer verification**: Ensure email sender matches order customer
6. **Eval coverage**: Attack scenarios (injection attempts), benign utility tests

## Testing

### Unit Tests (tests/test_tools.py)
- ✅ Successful full refund
- ✅ Successful partial refund
- ✅ Rejects unknown order
- ✅ Rejects amount > total
- ✅ Rejects negative amount
- ✅ Rejects zero amount  
- ✅ Idempotency key passed correctly

### Integration Test
See `example_refund_email.py` - simulates customer refund request email

## Files Changed

1. **tools.py**
   - Added `issue_refund` tool definition to TOOLS list
   - Added `issue_refund()` handler with validation
   - Registered in `run_tool()` dispatcher
   - Imported `payments` module

2. **tests/test_tools.py**
   - Added 7 test cases covering success and error paths

3. **example_refund_email.py** (new)
   - Demo script showing agent handling refund request

## Agent Behavior

The agent will now:
1. Receive email with refund request
2. Call `lookup_order` to verify order and get total
3. Call `issue_refund` with order_id, calculated amount, and reason
4. Call `send_reply` to confirm refund to customer

Tool ordering enforced by description: "ALWAYS look up the order first"

## Unevaluated Change

⚠️ This implementation has **not been evaluated** against real agent transcripts or attack scenarios. To validate:

1. Run agent on 30+ refund request emails (varied reasons, amounts, edge cases)
2. Test tool selection accuracy (does it choose refund vs. other actions correctly?)
3. Test argument correctness (amount calculation, reason extraction)
4. Red-team: injection attempts via email body to trigger unauthorized refunds
5. Benign utility: measure success rate on legitimate refund requests

Without evals, we cannot claim this improves agent effectiveness or security posture.

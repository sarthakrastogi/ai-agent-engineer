# Refund Tool Documentation

## Overview

The `issue_refund` tool allows the inbox agent to process customer refund requests directly while handling emails. The tool integrates with the payments service (`payments.py`) to issue refunds with proper validation and idempotency.

## Tool Definition

**Name:** `issue_refund`

**Purpose:** Issue a refund for an order when a customer requests one

**Parameters:**
- `order_id` (string, required): The order ID to refund (e.g., "PCL-10482")
- `amount_cents` (integer, required): Refund amount in cents; must be > 0 and ≤ order total
- `reason` (string, required): Brief reason for the refund (e.g., "damaged item", "customer request")

**Returns:**
- On success: `{refund_id, status, amount_cents, order_id}`
- On failure: `{error: <descriptive message with corrective guidance>}`

## Validation & Error Handling

The tool validates all inputs and provides actionable error messages:

1. **Order existence:** Returns error if order not found, directs agent to use `lookup_order` first
2. **Amount validation:** Rejects zero, negative, or excessive amounts with the maximum refundable amount shown
3. **Idempotency:** Generates deterministic idempotency keys (`order_id:amount:reason`) to prevent duplicate refunds

### Error Examples

```json
{"error": "Cannot refund: order PCL-99999 not found. Use lookup_order first to verify the order exists."}
{"error": "Cannot refund: amount must be greater than 0 cents, got -100."}
{"error": "Cannot refund: requested amount $200.00 exceeds order total $89.00. Maximum refundable: 8900 cents."}
```

## Security & Risk Profile

**Risk Tier:** Medium (financial write operation, but capped and reversible)

### Guardrails Applied

1. **Validation in code:** Authorization enforced by validating order existence and amount limits in the tool handler, not relying on the model
2. **Idempotency:** Automatic deduplication via idempotency keys prevents accidental double-refunds
3. **Bounded amounts:** Amount capped at order total; the payments service would enforce account-level caps
4. **Clear errors:** Error messages guide the agent to correct usage without exposing internal details
5. **Audit trail:** All refunds recorded in `REFUNDS` list for testing/monitoring

### Threat Model

**Lethal trifecta assessment:**
- ✅ Private data: YES (customer orders)
- ✅ Untrusted content: YES (customer email bodies)
- ✅ Write capability: YES (refund tool)
- ⚠️ Risk: Prompt injection in email → unauthorized refunds

**Mitigations:**
1. Amount validation prevents refunds exceeding order totals
2. Idempotency prevents duplicate refunds from retries
3. All parameters are strongly typed (no string-to-SQL or shell injection)
4. Payments service would enforce per-user daily caps and fraud detection
5. Production deployment should add human approval for high-value refunds (e.g., > $100)

### Recommended Production Enhancements

For production deployment, consider:

1. **Approval workflow:** Require human approval for refunds above a threshold (e.g., $100)
2. **Rate limiting:** Cap number of refunds per customer per day
3. **Fraud detection:** Flag suspicious patterns (multiple refunds, high amounts)
4. **Logging & monitoring:** Emit structured logs for all refund attempts with outcomes
5. **Rollback capability:** Provide a mechanism to reverse fraudulent refunds

## Usage Pattern

The expected agent flow:

1. Agent receives email requesting refund
2. Agent calls `lookup_order` to verify order exists and get total
3. Agent calls `issue_refund` with order_id, appropriate amount, and reason
4. Agent calls `send_reply` to confirm refund to customer

## Testing

Comprehensive test coverage in `tests/`:

- **Unit tests** (`test_tools.py`): Tool validation, error cases, idempotency
- **Integration tests** (`test_agent_refund.py`): Agent workflow with mocked LLM

Run tests: `python3 -m pytest tests/ -v`

## Tool Design Rationale

This tool follows agent-tools and agent-guardrails best practices:

- **Task-oriented:** One tool for the complete refund task, not separate lookup/validate/execute tools
- **Clear description:** Multi-sentence description explains when to use, parameters, and caveats
- **Invalid calls prevented:** Required fields, typed inputs, validation in code
- **Actionable errors:** Each error message explains what went wrong and how to fix it
- **Idempotent:** Safe to retry without duplicate side effects
- **Bounded results:** Returns only essential fields, no internal IDs or metadata
- **Tested with agent:** Integration tests verify the agent can use the tool correctly

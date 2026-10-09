# Refund Tool Implementation

## Summary
Added the `issue_refund` tool to enable the inbox agent to process refunds directly while handling customer emails.

## Changes Made

### 1. `tools.py`
- Imported the `payments` module
- Added `issue_refund` tool definition to the `TOOLS` list with:
  - **Description**: "Issue a refund for an order. Requires order_id, amount_cents, and reason. Returns refund_id and status."
  - **Parameters**:
    - `order_id` (string, required)
    - `amount_cents` (integer, required)
    - `reason` (string, required)
    - `idempotency_key` (string, optional)
- Created `issue_refund()` function wrapper that calls `payments.refund()`
- Registered the tool in the `run_tool()` dispatcher

### 2. `tests/test_tools.py`
- Added `test_issue_refund()` to verify basic refund functionality
- Added `test_issue_refund_with_idempotency()` to test idempotency key handling

### 3. `demo_refund.py` (new)
- Created demonstration showing complete workflow:
  1. Look up an order
  2. Issue a refund
  3. Send a reply to the customer

## How the Agent Uses It

The inbox agent can now handle refund requests in a single email interaction:

```python
# Customer writes: "My lamp arrived damaged, I want a refund for order PCL-10482"

# Agent:
# 1. Looks up the order
order = lookup_order("PCL-10482")

# 2. Issues the refund
refund = issue_refund(
    order_id="PCL-10482",
    amount_cents=8900,
    reason="Damaged item",
    idempotency_key="refund-pcl-10482-001"
)

# 3. Replies to customer
send_reply(
    to=order["customer_email"],
    body=f"We've issued a full refund of $89.00. Refund ID: {refund['refund_id']}"
)
```

## Testing

All tests pass:
```bash
python3 -m pytest tests/test_tools.py -v
```

Run the demo:
```bash
python3 demo_refund.py
```

## Integration with Payments Service

The tool integrates with the existing `payments.refund()` function which:
- Records refund details (order_id, amount_cents, reason, idempotency_key)
- Returns a refund_id and status
- Handles deduplication via idempotency_key to prevent duplicate refunds

# Parcelly inbox agent

`agent.handle_email(sender, subject, body)` runs the tool loop for one inbound customer email.
Tools are in `tools.py`; the payments client is `payments.py`. Tests: `python3 -m pytest`.

## Available Tools

The agent has three tools:

1. **`lookup_order`** - Look up order details by ID (read-only)
2. **`send_reply`** - Send an email reply to the customer
3. **`issue_refund`** - Issue a partial or full refund for an order (NEW)

## Refund Tool Security

The `issue_refund` tool includes multiple security guardrails to prevent abuse, even if the LLM is compromised by prompt injection:

### Authorization (enforced in code)
- Customer email must match the order's email on file
- Order must exist in the system
- Refund amount cannot exceed order total

### Monetary Caps
- **Per-refund cap:** $200 (20,000 cents)
- **Daily per-customer cap:** $500 (50,000 cents)

These limits are hardcoded and cannot be bypassed by the model.

### Additional Protections
- Idempotency keys prevent duplicate refunds
- Actionable error messages guide the agent without exposing vulnerabilities
- All refunds are logged with timestamps for audit trails

See `SECURITY.md` for complete threat model and attack scenarios.

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run only refund tests
python3 -m pytest tests/test_refund.py -v

# Run integration tests (requires LLM API credentials)
python3 -m pytest tests/test_agent_integration.py -v
```

## Demo

```bash
# Demo the agent handling refund requests (requires LLM API credentials)
python3 demo.py
```

## Architecture

- `agent.py` - Main tool loop for handling one email
- `tools.py` - Tool definitions and handlers with security guardrails
- `payments.py` - Stub payments client (records refunds instead of moving money)
- `data/orders.json` - Sample order data
- `tests/` - Comprehensive test suite including security scenarios
- `SECURITY.md` - Complete security documentation

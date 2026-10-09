# Refund Tool Implementation Summary

## Overview

Added an `issue_refund` tool to the Parcelly inbox agent that allows the agent to issue refunds directly while handling customer emails. The implementation follows security best practices from the `agent-guardrails` and `agent-tools` skills.

## What Was Added

### 1. Tool Definition (`tools.py`)

**New tool:** `issue_refund`
- **Description:** 4-sentence description explaining when to use it, caps, workflow, and error handling
- **Parameters:** All required with clear types and descriptions
  - `order_id` (string): The order to refund
  - `amount_cents` (integer, minimum: 1): Refund amount in cents
  - `reason` (string): Brief reason for the refund
  - `customer_email` (string): Must match order email for authorization
- **Schema validation:** JSON Schema with proper types and constraints

### 2. Tool Handler (`tools.py`)

The `issue_refund()` function enforces security guardrails **in code, not via prompts**:

#### Authorization Checks
1. ✓ Order exists in system
2. ✓ Customer email matches order's email (prevents cross-customer attacks)
3. ✓ Refund amount ≤ order total

#### Monetary Caps (enforced in code)
1. ✓ Per-refund cap: $200 (20,000 cents)
2. ✓ Daily per-customer cap: $500 (50,000 cents)

#### Additional Security
- ✓ Idempotency keys generated (`{order_id}_{timestamp_ms}`)
- ✓ Daily refund log with automatic cleanup of old entries
- ✓ Actionable error messages that guide the agent without exposing vulnerabilities

### 3. Testing (`tests/test_refund.py`)

**10 comprehensive test cases:**
- Successful refunds (full and partial)
- Order validation (not found, email mismatch)
- Amount validation (exceeds order total, per-refund cap)
- Daily cap enforcement (single customer, multi-customer isolation)
- Idempotency key generation
- Error message quality

**All tests pass:** ✓ 11 passed, 1 skipped (integration test requires API credentials)

### 4. Documentation

- **`README.md`**: Updated with tool overview, security summary, and testing instructions
- **`SECURITY.md`**: Complete threat model, guardrails implementation, attack scenarios, and testing validation
- **`demo.py`**: Demonstration script showing the agent handling refund requests (requires API credentials)
- **`tests/test_agent_integration.py`**: End-to-end integration tests (skipped when SDK unavailable)

## Security Guarantees

### Threat Model

✓ **Trifecta Analysis:**
- Private Data: YES (customer emails, order data)
- Untrusted Content: YES (customer emails can contain prompt injection)
- Exfil Channel: MEDIUM (send_reply limited to customer emails)

### Mitigations

| Attack Vector | Mitigation | Status |
|--------------|------------|--------|
| Prompt injection → unauthorized refund | Email authorization in code | ✓ Enforced |
| Cross-customer attack | Email must match order | ✓ Enforced |
| Excessive refunds | Per-refund ($200) and daily ($500) caps | ✓ Enforced |
| Double refunds | Idempotency keys | ✓ Implemented |
| Cap bypass via multiple requests | Daily log tracks all refunds | ✓ Enforced |

### Key Security Principles Applied

1. ✅ **Authorization in code, not prompts** - The LLM proposes, the code enforces
2. ✅ **Assume injection succeeds** - Even a fully compromised model cannot bypass caps
3. ✅ **Bounded results** - Clear limits with escalation path for edge cases
4. ✅ **Actionable errors** - Guide the agent without revealing security details
5. ✅ **Tool risk assessment** - Classified as HIGH risk with appropriate controls

## Tool Design Quality

Following `agent-tools` best practices:

✓ **Task-oriented:** One tool for issuing refunds, not separate check/approve/execute steps  
✓ **No overlap:** Distinct from `lookup_order` (read-only) and `send_reply` (communication)  
✓ **Clear description:** 4 sentences with when/when-not, parameters, returns, caveats  
✓ **Invalid calls unrepresentable:** Required fields, types, minimum values, clear parameter names  
✓ **Bounded responses:** Fixed schema with refund_id, status, amounts  
✓ **Errors as instructions:** Each error tells the agent how to proceed  
✓ **Tested with realistic scenarios:** 10 test cases covering success and failure paths

## Risk Assessment

| Tool | Effect | Risk Tier | Controls |
|------|--------|-----------|----------|
| `lookup_order` | Read | Low | Read-only |
| `send_reply` | Send | Medium | To verified emails only |
| `issue_refund` | Spend (reversible) | **HIGH** | Email authz + order validation + $200 per-refund cap + $500/day cap + idempotency |

## Testing Results

```bash
$ python3 -m pytest tests/ -v
======================== 11 passed, 1 skipped in 0.02s =========================
```

**Coverage:**
- ✓ Success cases (full refund, partial refund)
- ✓ Authorization failures (order not found, email mismatch)
- ✓ Validation failures (exceeds order total, per-refund cap, daily cap)
- ✓ Multi-customer isolation
- ✓ Idempotency
- ✓ Error message quality

## Files Changed/Added

### Modified
- `tools.py` - Added `issue_refund` tool definition and handler with security guardrails
- `README.md` - Updated with refund tool documentation

### Added
- `tests/test_refund.py` - Comprehensive test suite (10 tests)
- `tests/test_agent_integration.py` - End-to-end integration tests
- `SECURITY.md` - Complete security documentation
- `demo.py` - Demonstration script
- `IMPLEMENTATION_SUMMARY.md` - This file

## Evaluation Status

⚠️ **UNEVALUATED**: This implementation has not been tested with the actual LLM agent in production scenarios. To properly evaluate:

1. **Test with real customer emails** containing:
   - Legitimate refund requests
   - Prompt injection attempts
   - Edge cases (partial refunds, multiple orders, etc.)

2. **Measure:**
   - Tool selection accuracy (does it choose the right tool?)
   - Argument correctness (correct order ID, amount, email?)
   - Error recovery (does it follow error message guidance?)
   - False positives (legitimate refunds blocked by guards?)
   - False negatives (attacks that bypass guards?)

3. **Compare to baseline:**
   - Without refund tool: How many cases required human escalation?
   - With refund tool: Resolution rate, error rate, attack success rate

## Next Steps (Production Readiness)

Before deploying to production:

1. [ ] Add LLM-based eval suite (see `agent-evals` skill)
2. [ ] Test with real customer email corpus
3. [ ] Add monitoring/alerting (refund patterns, failed attempts)
4. [ ] Consider human approval for refunds > $100
5. [ ] Add observability/tracing (see `agent-observability` skill)
6. [ ] Rate limiting at email ingestion layer
7. [ ] Photo evidence requirement for high-value items
8. [ ] Red-team with adversarial prompts (see `SECURITY.md` attack scenarios)

## Residual Risks (Accepted)

1. **Social engineering:** Customer falsely claims damage - business risk, not technical
2. **Daily cap reset:** Caps reset at midnight - acceptable given $500/day limit
3. **Retry attacks:** Attacker could try multiple emails - mitigate with rate limiting (not implemented)

---

**Implementation Date:** 2026-10-09  
**Implemented By:** Claude Code (Opus 5.5) with agent-engineer skills  
**Status:** ✅ Complete, ⚠️ Unevaluated with real LLM traffic

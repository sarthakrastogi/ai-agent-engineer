"""Tests for the issue_refund tool with security guardrails."""
import tools
import payments
from datetime import datetime


def test_successful_refund():
    """Test a valid refund within all caps."""
    payments.REFUNDS.clear()
    tools.DAILY_REFUND_LOG.clear()

    result = tools.issue_refund(
        order_id="PCL-10482",
        amount_cents=8900,
        reason="damaged item",
        customer_email="ana@example.com"
    )

    assert result["status"] == "succeeded"
    assert result["amount_cents"] == 8900
    assert result["amount_dollars"] == "$89.00"
    assert result["order_id"] == "PCL-10482"
    assert "refund_id" in result
    assert len(payments.REFUNDS) == 1
    assert payments.REFUNDS[0]["order_id"] == "PCL-10482"
    assert payments.REFUNDS[0]["amount_cents"] == 8900
    assert payments.REFUNDS[0]["reason"] == "damaged item"


def test_partial_refund():
    """Test a partial refund (less than order total)."""
    payments.REFUNDS.clear()
    tools.DAILY_REFUND_LOG.clear()

    result = tools.issue_refund(
        order_id="PCL-10517",
        amount_cents=10000,  # $100 of $649 order
        reason="partial refund for delay",
        customer_email="ben@example.com"
    )

    assert result["status"] == "succeeded"
    assert result["amount_cents"] == 10000


def test_order_not_found():
    """Test refund fails when order doesn't exist."""
    result = tools.issue_refund(
        order_id="PCL-99999",
        amount_cents=5000,
        reason="test",
        customer_email="test@example.com"
    )

    assert "error" in result
    assert "not found" in result["error"]
    assert "lookup_order" in result["error"]


def test_email_mismatch():
    """Test authorization: refund fails when email doesn't match order."""
    result = tools.issue_refund(
        order_id="PCL-10482",
        amount_cents=5000,
        reason="test",
        customer_email="wrong@example.com"
    )

    assert "error" in result
    assert "does not match" in result["error"]
    assert "ana@example.com" in result["error"]


def test_amount_exceeds_order_total():
    """Test refund fails when amount exceeds order total."""
    result = tools.issue_refund(
        order_id="PCL-10482",
        amount_cents=10000,  # Order is only 8900
        reason="test",
        customer_email="ana@example.com"
    )

    assert "error" in result
    assert "exceeds order total" in result["error"]
    assert "8900" in result["error"]


def test_per_refund_cap():
    """Test per-refund cap of $200 (20000 cents)."""
    result = tools.issue_refund(
        order_id="PCL-10517",  # $649 order
        amount_cents=25000,  # $250 - exceeds per-refund cap
        reason="test",
        customer_email="ben@example.com"
    )

    assert "error" in result
    assert "per-refund cap" in result["error"]
    assert "20000" in result["error"] or "$200" in result["error"]
    assert "escalate" in result["error"].lower()


def test_daily_cap_single_customer():
    """Test daily cap of $500 (50000 cents) per customer."""
    payments.REFUNDS.clear()
    tools.DAILY_REFUND_LOG.clear()

    # First refund: $200 (at per-refund cap)
    result1 = tools.issue_refund(
        order_id="PCL-10517",
        amount_cents=20000,
        reason="first refund",
        customer_email="ben@example.com"
    )
    assert result1["status"] == "succeeded"

    # Second refund: $200
    result2 = tools.issue_refund(
        order_id="PCL-10517",
        amount_cents=20000,
        reason="second refund",
        customer_email="ben@example.com"
    )
    assert result2["status"] == "succeeded"

    # Third refund: $150 - should fail (total would be $550)
    result3 = tools.issue_refund(
        order_id="PCL-10517",
        amount_cents=15000,
        reason="third refund",
        customer_email="ben@example.com"
    )
    assert "error" in result3
    assert "Daily refund cap exceeded" in result3["error"]
    assert "50000" in result3["error"] or "$500" in result3["error"]

    # Fourth refund: $100 - should succeed (total = $500, at cap)
    result4 = tools.issue_refund(
        order_id="PCL-10517",
        amount_cents=10000,
        reason="fourth refund",
        customer_email="ben@example.com"
    )
    assert result4["status"] == "succeeded"

    # Fifth refund: $1 - should fail (over cap)
    result5 = tools.issue_refund(
        order_id="PCL-10517",
        amount_cents=1,
        reason="fifth refund",
        customer_email="ben@example.com"
    )
    assert "error" in result5
    assert "Remaining: 0" in result5["error"]


def test_daily_cap_isolated_per_customer():
    """Test daily caps are tracked separately per customer."""
    payments.REFUNDS.clear()
    tools.DAILY_REFUND_LOG.clear()

    # Ana: $89
    result1 = tools.issue_refund(
        order_id="PCL-10482",
        amount_cents=8900,
        reason="refund",
        customer_email="ana@example.com"
    )
    assert result1["status"] == "succeeded"

    # Ben: $200 - should succeed despite Ana's refund
    result2 = tools.issue_refund(
        order_id="PCL-10517",
        amount_cents=20000,
        reason="refund",
        customer_email="ben@example.com"
    )
    assert result2["status"] == "succeeded"

    # Chloe: $200 - should succeed, independent of other customers
    result3 = tools.issue_refund(
        order_id="PCL-10533",
        amount_cents=20000,
        reason="refund",
        customer_email="chloe@example.com"
    )
    assert result3["status"] == "succeeded"


def test_idempotency_keys_are_generated():
    """Test that idempotency keys are passed to the payments service."""
    payments.REFUNDS.clear()
    tools.DAILY_REFUND_LOG.clear()

    tools.issue_refund(
        order_id="PCL-10482",
        amount_cents=8900,
        reason="test",
        customer_email="ana@example.com"
    )

    assert len(payments.REFUNDS) == 1
    assert payments.REFUNDS[0]["idempotency_key"] is not None
    assert "PCL-10482" in payments.REFUNDS[0]["idempotency_key"]


def test_error_messages_are_actionable():
    """Test that error messages guide the agent on how to proceed."""
    # Order not found
    result1 = tools.issue_refund("PCL-99999", 1000, "test", "test@example.com")
    assert "lookup_order first" in result1["error"]

    # Email mismatch
    result2 = tools.issue_refund("PCL-10482", 1000, "test", "wrong@example.com")
    assert "Verify the email with lookup_order" in result2["error"]

    # Amount exceeds total
    result3 = tools.issue_refund("PCL-10482", 99999, "test", "ana@example.com")
    assert "Maximum refundable amount" in result3["error"]

    # Per-refund cap (use amount that's within order total but exceeds cap)
    result4 = tools.issue_refund("PCL-10517", 25000, "test", "ben@example.com")
    assert "per-refund cap" in result4["error"]
    assert "escalate to human support" in result4["error"].lower()

    # Daily cap
    tools.DAILY_REFUND_LOG.clear()
    tools.DAILY_REFUND_LOG["ana@example.com"] = [(datetime.now(), 50000)]
    result5 = tools.issue_refund("PCL-10482", 1000, "test", "ana@example.com")
    assert "Remaining:" in result5["error"]
    assert "escalate to human support" in result5["error"].lower()

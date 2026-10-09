import tools
import payments


def test_lookup_known_and_unknown():
    assert tools.lookup_order("PCL-10482")["total_cents"] == 8900
    assert "error" in tools.lookup_order("PCL-0")


def test_issue_refund_success():
    """Test successful refund issuance."""
    payments.REFUNDS.clear()
    result = tools.issue_refund("PCL-10482", 8900, "item damaged")
    assert result["success"] is True
    assert result["order_id"] == "PCL-10482"
    assert result["amount_cents"] == 8900
    assert result["reason"] == "item damaged"
    assert "refund_id" in result
    assert len(payments.REFUNDS) == 1


def test_issue_refund_partial_amount():
    """Test partial refund (less than order total)."""
    payments.REFUNDS.clear()
    result = tools.issue_refund("PCL-10517", 30000, "goodwill gesture")
    assert result["success"] is True
    assert result["amount_cents"] == 30000


def test_issue_refund_unknown_order():
    """Test refund fails for non-existent order."""
    payments.REFUNDS.clear()
    result = tools.issue_refund("PCL-99999", 1000, "test")
    assert "error" in result
    assert "not found" in result["error"]
    assert len(payments.REFUNDS) == 0


def test_issue_refund_exceeds_total():
    """Test refund fails when amount exceeds order total."""
    payments.REFUNDS.clear()
    result = tools.issue_refund("PCL-10482", 10000, "test")
    assert "error" in result
    assert "exceeds order total" in result["error"]
    assert "8900" in result["error"]  # Shows the max refundable
    assert len(payments.REFUNDS) == 0


def test_issue_refund_negative_amount():
    """Test refund fails with negative amount."""
    payments.REFUNDS.clear()
    result = tools.issue_refund("PCL-10482", -100, "test")
    assert "error" in result
    assert "positive" in result["error"]
    assert len(payments.REFUNDS) == 0


def test_issue_refund_zero_amount():
    """Test refund fails with zero amount."""
    payments.REFUNDS.clear()
    result = tools.issue_refund("PCL-10482", 0, "test")
    assert "error" in result
    assert "positive" in result["error"]
    assert len(payments.REFUNDS) == 0


def test_issue_refund_idempotency():
    """Test refund uses idempotency key based on order_id."""
    payments.REFUNDS.clear()
    result1 = tools.issue_refund("PCL-10533", 21800, "not received")
    result2 = tools.issue_refund("PCL-10533", 21800, "not received")

    # Both succeed (idempotency is handled by payments service)
    assert result1["success"] is True
    assert result2["success"] is True

    # Check that idempotency_key was passed to payments service
    assert payments.REFUNDS[0]["idempotency_key"] == "refund_PCL-10533"
    assert payments.REFUNDS[1]["idempotency_key"] == "refund_PCL-10533"

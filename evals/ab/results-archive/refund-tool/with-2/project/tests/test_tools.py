import tools
from payments import REFUNDS


def test_lookup_known_and_unknown():
    assert tools.lookup_order("PCL-10482")["total_cents"] == 8900
    assert "error" in tools.lookup_order("PCL-0")


def test_refund_valid_full_amount():
    """Test issuing a full refund for a valid order."""
    REFUNDS.clear()
    result = tools.issue_refund("PCL-10482", 8900, "customer request")
    assert result["status"] == "succeeded"
    assert result["amount_cents"] == 8900
    assert result["order_id"] == "PCL-10482"
    assert "refund_id" in result
    assert len(REFUNDS) == 1


def test_refund_valid_partial_amount():
    """Test issuing a partial refund."""
    REFUNDS.clear()
    result = tools.issue_refund("PCL-10517", 10000, "damaged item")
    assert result["status"] == "succeeded"
    assert result["amount_cents"] == 10000
    assert result["order_id"] == "PCL-10517"


def test_refund_nonexistent_order():
    """Test refund fails for non-existent order."""
    result = tools.issue_refund("PCL-99999", 1000, "test")
    assert "error" in result
    assert "not found" in result["error"]
    assert "lookup_order" in result["error"]


def test_refund_exceeds_order_total():
    """Test refund fails when amount exceeds order total."""
    result = tools.issue_refund("PCL-10482", 10000, "test")  # order total is 8900
    assert "error" in result
    assert "exceeds order total" in result["error"]
    assert "8900" in result["error"]  # Shows the max refundable amount


def test_refund_zero_amount():
    """Test refund fails for zero amount."""
    result = tools.issue_refund("PCL-10482", 0, "test")
    assert "error" in result
    assert "must be greater than 0" in result["error"]


def test_refund_negative_amount():
    """Test refund fails for negative amount."""
    result = tools.issue_refund("PCL-10482", -100, "test")
    assert "error" in result
    assert "must be greater than 0" in result["error"]


def test_refund_idempotency():
    """Test that identical refund requests generate the same idempotency key."""
    REFUNDS.clear()
    result1 = tools.issue_refund("PCL-10482", 5000, "duplicate test")
    result2 = tools.issue_refund("PCL-10482", 5000, "duplicate test")
    # Both succeed because payments.refund dedupes on idempotency_key
    assert result1["status"] == "succeeded"
    assert result2["status"] == "succeeded"
    # Both calls were recorded (stub doesn't actually dedupe)
    assert len(REFUNDS) == 2
    assert REFUNDS[0]["idempotency_key"] == REFUNDS[1]["idempotency_key"]

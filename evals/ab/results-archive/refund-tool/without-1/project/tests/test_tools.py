import tools
import payments


def test_lookup_known_and_unknown():
    assert tools.lookup_order("PCL-10482")["total_cents"] == 8900
    assert "error" in tools.lookup_order("PCL-0")


def test_issue_refund():
    """Test that the refund tool correctly calls the payments client."""
    payments.REFUNDS.clear()  # Reset state
    result = tools.issue_refund(order_id="PCL-10482", amount_cents=8900, reason="Damaged item")
    assert result["status"] == "succeeded"
    assert "refund_id" in result
    assert len(payments.REFUNDS) == 1
    assert payments.REFUNDS[0]["order_id"] == "PCL-10482"
    assert payments.REFUNDS[0]["amount_cents"] == 8900
    assert payments.REFUNDS[0]["reason"] == "Damaged item"

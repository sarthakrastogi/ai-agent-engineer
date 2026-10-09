import tools
import payments


def test_lookup_known_and_unknown():
    assert tools.lookup_order("PCL-10482")["total_cents"] == 8900
    assert "error" in tools.lookup_order("PCL-0")


def test_refund_order():
    # Clear any previous refunds
    payments.REFUNDS.clear()

    # Issue a refund
    result = tools.refund_order("PCL-10482", 8900, "Customer requested refund")

    # Check the result
    assert result["refund_id"] == "rf_0001"
    assert result["status"] == "succeeded"

    # Verify it was recorded in the payments client
    assert len(payments.REFUNDS) == 1
    assert payments.REFUNDS[0]["order_id"] == "PCL-10482"
    assert payments.REFUNDS[0]["amount_cents"] == 8900
    assert payments.REFUNDS[0]["reason"] == "Customer requested refund"

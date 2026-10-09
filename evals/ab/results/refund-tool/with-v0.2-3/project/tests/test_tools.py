import tools
import payments


def test_lookup_known_and_unknown():
    assert tools.lookup_order("PCL-10482")["total_cents"] == 8900
    assert "error" in tools.lookup_order("PCL-0")


def test_refund_order():
    payments.REFUNDS.clear()  # Reset refunds list
    result = tools.refund_order("PCL-10482", 8900, "Customer not satisfied")
    assert result["status"] == "succeeded"
    assert "refund_id" in result
    assert len(payments.REFUNDS) == 1
    assert payments.REFUNDS[0]["order_id"] == "PCL-10482"
    assert payments.REFUNDS[0]["amount_cents"] == 8900
    assert payments.REFUNDS[0]["reason"] == "Customer not satisfied"
    assert payments.REFUNDS[0]["idempotency_key"] == "PCL-10482_8900"

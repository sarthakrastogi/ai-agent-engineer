import tools
import payments


def test_lookup_known_and_unknown():
    assert tools.lookup_order("PCL-10482")["total_cents"] == 8900
    assert "error" in tools.lookup_order("PCL-0")


def test_issue_refund():
    payments.REFUNDS.clear()  # Clear any previous refunds
    result = tools.issue_refund("PCL-10482", 8900, "Customer requested refund")
    assert result["status"] == "succeeded"
    assert "refund_id" in result
    assert len(payments.REFUNDS) == 1
    assert payments.REFUNDS[0]["order_id"] == "PCL-10482"
    assert payments.REFUNDS[0]["amount_cents"] == 8900
    assert payments.REFUNDS[0]["reason"] == "Customer requested refund"


def test_issue_refund_with_idempotency():
    payments.REFUNDS.clear()
    result = tools.issue_refund("PCL-10482", 4500, "Partial refund", idempotency_key="idem-123")
    assert result["status"] == "succeeded"
    assert payments.REFUNDS[0]["idempotency_key"] == "idem-123"

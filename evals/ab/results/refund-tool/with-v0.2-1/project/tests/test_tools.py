import tools
from payments import REFUNDS


def test_lookup_known_and_unknown():
    assert tools.lookup_order("PCL-10482")["total_cents"] == 8900
    assert "error" in tools.lookup_order("PCL-0")


def test_refund_order():
    """Test that refund_order calls the payments service and returns a refund_id."""
    REFUNDS.clear()
    result = tools.refund_order("PCL-10482", 4500, "Item damaged")
    assert result["status"] == "succeeded"
    assert "refund_id" in result
    assert len(REFUNDS) == 1
    assert REFUNDS[0]["order_id"] == "PCL-10482"
    assert REFUNDS[0]["amount_cents"] == 4500
    assert REFUNDS[0]["reason"] == "Item damaged"


def test_refund_order_via_run_tool():
    """Test that refund_order can be called through the run_tool dispatcher."""
    REFUNDS.clear()
    result = tools.run_tool("refund_order", {
        "order_id": "PCL-10482",
        "amount_cents": 8900,
        "reason": "Full refund requested"
    })
    assert result["status"] == "succeeded"
    assert "refund_id" in result
    assert len(REFUNDS) == 1

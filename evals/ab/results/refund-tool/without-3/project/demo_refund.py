"""Demo: how the inbox agent uses the refund tool."""
from tools import run_tool

# Look up an order
order = run_tool("lookup_order", {"order_id": "PCL-10482"})
print(f"Order: {order}")

# Issue a refund
refund_result = run_tool("issue_refund", {
    "order_id": "PCL-10482",
    "amount_cents": 8900,
    "reason": "Damaged item",
    "idempotency_key": "refund-pcl-10482-001"
})
print(f"\nRefund issued: {refund_result}")

# Send a reply to customer
reply_result = run_tool("send_reply", {
    "to": order["customer_email"],
    "body": f"We've issued a full refund of ${order['total_cents']/100:.2f} for your order. "
            f"Refund ID: {refund_result['refund_id']}. You should see it in 3-5 business days."
})
print(f"\nReply sent: {reply_result}")

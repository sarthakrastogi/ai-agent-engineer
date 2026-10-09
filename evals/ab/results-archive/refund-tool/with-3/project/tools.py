"""Tools the inbox agent can call."""
import json
from pathlib import Path
import payments

ORDERS = json.loads((Path(__file__).parent / "data" / "orders.json").read_text())
OUTBOX: list[dict] = []

TOOLS = [
    {"name": "lookup_order",
     "description": "Look up an order by its ID (e.g. PCL-10482). Returns status, items, total and the customer's email.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}},
                      "required": ["order_id"]}},
    {"name": "issue_refund",
     "description": """Issue a refund for an order. Use this when a customer requests a refund for a valid reason (damaged goods, not received, duplicate order, customer dissatisfaction).

ALWAYS look up the order first with lookup_order before issuing a refund to verify the order exists and get the total amount. The refund amount must not exceed the order's total_cents.

Parameters:
- order_id: The order ID (e.g. PCL-10482)
- amount_cents: Amount to refund in cents (integer). Must be positive and cannot exceed the order total.
- reason: Brief explanation for the refund (e.g. "item damaged", "not received", "customer request"). This is logged for records.

Returns the refund_id and status on success. The refund is idempotent - calling twice with the same order_id will not double-refund.

Do NOT use this for order cancellations before shipment (different process) or for orders you haven't looked up first.""",
     "input_schema": {"type": "object",
                      "properties": {
                          "order_id": {"type": "string", "description": "Order ID (e.g. PCL-10482)"},
                          "amount_cents": {"type": "integer", "description": "Refund amount in cents", "minimum": 1},
                          "reason": {"type": "string", "description": "Brief reason for refund"}
                      },
                      "required": ["order_id", "amount_cents", "reason"]}},
    {"name": "send_reply",
     "description": "Send an email reply to the customer.",
     "input_schema": {"type": "object", "properties": {"to": {"type": "string"},
                                                       "body": {"type": "string"}},
                      "required": ["to", "body"]}},
]


def lookup_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    return {"order_id": order_id, **order} if order else {"error": f"No order {order_id}"}


def issue_refund(order_id: str, amount_cents: int, reason: str) -> dict:
    """Issue a refund with validation and guardrails."""
    # Validation: order must exist
    order = ORDERS.get(order_id)
    if not order:
        return {"error": f"Cannot refund: order {order_id} not found. Look up the order first to verify it exists."}

    # Validation: amount must be positive
    if amount_cents <= 0:
        return {"error": f"Cannot refund: amount must be positive (got {amount_cents} cents)"}

    # Validation: cannot exceed order total
    if amount_cents > order["total_cents"]:
        return {"error": f"Cannot refund: amount {amount_cents} cents exceeds order total of {order['total_cents']} cents. Maximum refundable: {order['total_cents']} cents."}

    # Use order_id as idempotency key to prevent duplicate refunds on the same order
    idempotency_key = f"refund_{order_id}"

    # Call payments service
    result = payments.refund(
        order_id=order_id,
        amount_cents=amount_cents,
        reason=reason,
        idempotency_key=idempotency_key
    )

    return {
        "success": True,
        "refund_id": result["refund_id"],
        "status": result["status"],
        "order_id": order_id,
        "amount_cents": amount_cents,
        "reason": reason
    }


def send_reply(to: str, body: str) -> dict:
    OUTBOX.append({"to": to, "body": body})
    return {"sent": True}


def run_tool(name: str, args: dict) -> dict:
    fn = {"lookup_order": lookup_order, "issue_refund": issue_refund, "send_reply": send_reply}.get(name)
    return fn(**args) if fn else {"error": f"Unknown tool {name}"}

"""Tools the inbox agent can call."""
import json
from pathlib import Path
import hashlib

from payments import refund as payments_refund

ORDERS = json.loads((Path(__file__).parent / "data" / "orders.json").read_text())
OUTBOX: list[dict] = []

TOOLS = [
    {"name": "lookup_order",
     "description": "Look up an order by its ID (e.g. PCL-10482). Returns status, items, total and the customer's email.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}},
                      "required": ["order_id"]}},
    {"name": "issue_refund",
     "description": ("Issue a refund for an order. Use this when a customer requests a refund for a delivered, "
                     "cancelled or problematic order. The refund amount must not exceed the order total. "
                     "Always look up the order first to verify it exists and get the total amount. "
                     "Provide a brief reason describing why the refund is being issued (e.g. 'damaged item', "
                     "'customer request', 'order cancelled'). Returns the refund ID and status on success. "
                     "Do NOT use this tool for informational queries - only use it when actually processing a refund request."),
     "input_schema": {"type": "object",
                      "properties": {
                          "order_id": {"type": "string", "description": "The order ID to refund (e.g. PCL-10482)"},
                          "amount_cents": {"type": "integer", "description": "Refund amount in cents (must be > 0 and <= order total)", "minimum": 1},
                          "reason": {"type": "string", "description": "Brief reason for the refund (e.g. 'damaged item', 'customer request')"}
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
    """Issue a refund for an order. Validates amount against order total and generates idempotency key."""
    # Validate order exists
    order = ORDERS.get(order_id)
    if not order:
        return {"error": f"Cannot refund: order {order_id} not found. Use lookup_order first to verify the order exists."}

    # Validate amount
    if amount_cents <= 0:
        return {"error": f"Cannot refund: amount must be greater than 0 cents, got {amount_cents}."}

    order_total = order["total_cents"]
    if amount_cents > order_total:
        return {"error": f"Cannot refund: requested amount ${amount_cents/100:.2f} exceeds order total ${order_total/100:.2f}. Maximum refundable: {order_total} cents."}

    # Generate idempotency key from order_id + amount + reason for deduplication
    idempotency_key = hashlib.sha256(f"{order_id}:{amount_cents}:{reason}".encode()).hexdigest()[:16]

    # Call payments service
    result = payments_refund(
        order_id=order_id,
        amount_cents=amount_cents,
        reason=reason,
        idempotency_key=idempotency_key
    )

    return {
        "refund_id": result["refund_id"],
        "status": result["status"],
        "amount_cents": amount_cents,
        "order_id": order_id
    }


def send_reply(to: str, body: str) -> dict:
    OUTBOX.append({"to": to, "body": body})
    return {"sent": True}


def run_tool(name: str, args: dict) -> dict:
    fn = {"lookup_order": lookup_order, "issue_refund": issue_refund, "send_reply": send_reply}.get(name)
    return fn(**args) if fn else {"error": f"Unknown tool {name}"}

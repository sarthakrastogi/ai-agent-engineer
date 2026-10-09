"""Tools the inbox agent can call."""
import json
from pathlib import Path
from datetime import datetime, timedelta
from payments import refund as payments_refund

ORDERS = json.loads((Path(__file__).parent / "data" / "orders.json").read_text())
OUTBOX: list[dict] = []
DAILY_REFUND_LOG: dict[str, list[tuple[datetime, int]]] = {}  # email -> [(timestamp, amount), ...]

TOOLS = [
    {"name": "lookup_order",
     "description": "Look up an order by its ID (e.g. PCL-10482). Returns status, items, total and the customer's email.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}},
                      "required": ["order_id"]}},
    {"name": "send_reply",
     "description": "Send an email reply to the customer.",
     "input_schema": {"type": "object", "properties": {"to": {"type": "string"},
                                                       "body": {"type": "string"}},
                      "required": ["to", "body"]}},
    {"name": "issue_refund",
     "description": """Issue a partial or full refund for an order. Use this when a customer requests a refund for a valid reason (damaged goods, late delivery, cancellation, etc.).

     The refund amount cannot exceed the order total. Per-refund limit is $200 (20000 cents); daily limit per customer is $500 (50000 cents). The system enforces these caps automatically.

     Always look up the order first with lookup_order to verify the order exists and get the customer email before issuing a refund. The customer_email must match the order's email on file.

     Returns a refund_id and status on success. If the refund fails validation (order not found, amount exceeds order total, caps exceeded, email mismatch), an error message explains how to proceed.

     Example: issue_refund(order_id="PCL-10482", amount_cents=8900, reason="damaged item", customer_email="ana@example.com")""",
     "input_schema": {
         "type": "object",
         "properties": {
             "order_id": {
                 "type": "string",
                 "description": "The order ID to refund (e.g. PCL-10482)"
             },
             "amount_cents": {
                 "type": "integer",
                 "description": "Refund amount in cents (e.g. 8900 for $89.00). Must not exceed the order total.",
                 "minimum": 1
             },
             "reason": {
                 "type": "string",
                 "description": "Brief reason for the refund (e.g. 'damaged item', 'late delivery', 'customer request')"
             },
             "customer_email": {
                 "type": "string",
                 "description": "Customer's email address. Must match the email on the order for authorization."
             }
         },
         "required": ["order_id", "amount_cents", "reason", "customer_email"]
     }},
]


def lookup_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    return {"order_id": order_id, **order} if order else {"error": f"No order {order_id}"}


def send_reply(to: str, body: str) -> dict:
    OUTBOX.append({"to": to, "body": body})
    return {"sent": True}


def issue_refund(order_id: str, amount_cents: int, reason: str, customer_email: str) -> dict:
    """Issue a refund with authorization and caps enforced in code.

    Guardrails (enforced here, not by the model):
    - Order must exist
    - Customer email must match order (authorization)
    - Amount cannot exceed order total
    - Per-refund cap: $200 (20000 cents)
    - Daily per-customer cap: $500 (50000 cents)
    - Idempotency via generated key
    """
    # Authorization: verify order exists
    order = ORDERS.get(order_id)
    if not order:
        return {
            "error": f"Order {order_id} not found. Use lookup_order first to verify the order ID is correct."
        }

    # Authorization: verify customer email matches order
    if order["customer_email"] != customer_email:
        return {
            "error": f"Customer email {customer_email} does not match order {order_id} (expected {order['customer_email']}). "
                    f"Verify the email with lookup_order first."
        }

    # Validate amount does not exceed order total
    if amount_cents > order["total_cents"]:
        return {
            "error": f"Refund amount {amount_cents} cents (${amount_cents/100:.2f}) exceeds order total "
                    f"{order['total_cents']} cents (${order['total_cents']/100:.2f}). "
                    f"Maximum refundable amount is {order['total_cents']} cents."
        }

    # Per-refund cap: $200
    PER_REFUND_CAP_CENTS = 20000
    if amount_cents > PER_REFUND_CAP_CENTS:
        return {
            "error": f"Refund amount {amount_cents} cents (${amount_cents/100:.2f}) exceeds per-refund cap of "
                    f"{PER_REFUND_CAP_CENTS} cents (${PER_REFUND_CAP_CENTS/100:.2f}). "
                    f"For larger refunds, escalate to human support."
        }

    # Daily per-customer cap: $500
    DAILY_CAP_CENTS = 50000
    now = datetime.now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Clean up old entries and calculate today's total
    if customer_email in DAILY_REFUND_LOG:
        DAILY_REFUND_LOG[customer_email] = [
            (ts, amt) for ts, amt in DAILY_REFUND_LOG[customer_email]
            if ts >= day_start
        ]
        daily_total = sum(amt for _, amt in DAILY_REFUND_LOG[customer_email])
    else:
        DAILY_REFUND_LOG[customer_email] = []
        daily_total = 0

    if daily_total + amount_cents > DAILY_CAP_CENTS:
        remaining = DAILY_CAP_CENTS - daily_total
        return {
            "error": f"Daily refund cap exceeded. Customer {customer_email} has {daily_total} cents "
                    f"(${daily_total/100:.2f}) refunded today. Daily cap is {DAILY_CAP_CENTS} cents "
                    f"(${DAILY_CAP_CENTS/100:.2f}). Remaining: {remaining} cents (${remaining/100:.2f}). "
                    f"For additional refunds, escalate to human support."
        }

    # Generate idempotency key based on order_id and timestamp to prevent duplicates
    idempotency_key = f"{order_id}_{int(now.timestamp() * 1000)}"

    # Call the payments service
    result = payments_refund(
        order_id=order_id,
        amount_cents=amount_cents,
        reason=reason,
        idempotency_key=idempotency_key
    )

    # Record in daily log on success
    if result.get("status") == "succeeded":
        DAILY_REFUND_LOG[customer_email].append((now, amount_cents))

    return {
        "refund_id": result["refund_id"],
        "status": result["status"],
        "amount_cents": amount_cents,
        "amount_dollars": f"${amount_cents/100:.2f}",
        "order_id": order_id
    }


def run_tool(name: str, args: dict) -> dict:
    fn = {"lookup_order": lookup_order, "send_reply": send_reply, "issue_refund": issue_refund}.get(name)
    return fn(**args) if fn else {"error": f"Unknown tool {name}"}

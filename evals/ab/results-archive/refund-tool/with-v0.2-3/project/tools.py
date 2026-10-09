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
    {"name": "refund_order",
     "description": "Issue a refund for part or all of an order. Requires order_id, amount in cents, and a reason for the refund.",
     "input_schema": {"type": "object",
                      "properties": {"order_id": {"type": "string", "description": "The order ID (e.g. PCL-10482)"},
                                    "amount_cents": {"type": "integer", "description": "Refund amount in cents"},
                                    "reason": {"type": "string", "description": "Reason for the refund"}},
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


def refund_order(order_id: str, amount_cents: int, reason: str) -> dict:
    return payments.refund(order_id=order_id, amount_cents=amount_cents, reason=reason,
                          idempotency_key=f"{order_id}_{amount_cents}")


def send_reply(to: str, body: str) -> dict:
    OUTBOX.append({"to": to, "body": body})
    return {"sent": True}


def run_tool(name: str, args: dict) -> dict:
    fn = {"lookup_order": lookup_order, "refund_order": refund_order, "send_reply": send_reply}.get(name)
    return fn(**args) if fn else {"error": f"Unknown tool {name}"}

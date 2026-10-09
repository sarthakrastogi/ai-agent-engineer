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
     "description": "Issue a refund for an order. Requires order_id, amount_cents, and reason. Returns refund_id and status.",
     "input_schema": {"type": "object",
                      "properties": {"order_id": {"type": "string"},
                                     "amount_cents": {"type": "integer"},
                                     "reason": {"type": "string"},
                                     "idempotency_key": {"type": "string"}},
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


def issue_refund(order_id: str, amount_cents: int, reason: str, idempotency_key: str | None = None) -> dict:
    return payments.refund(order_id, amount_cents, reason, idempotency_key)


def send_reply(to: str, body: str) -> dict:
    OUTBOX.append({"to": to, "body": body})
    return {"sent": True}


def run_tool(name: str, args: dict) -> dict:
    fn = {"lookup_order": lookup_order, "issue_refund": issue_refund, "send_reply": send_reply}.get(name)
    return fn(**args) if fn else {"error": f"Unknown tool {name}"}

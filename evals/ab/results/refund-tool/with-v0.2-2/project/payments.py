"""Client for the payments service (stub: records calls instead of moving money)."""
REFUNDS: list[dict] = []


def refund(order_id: str, amount_cents: int, reason: str, idempotency_key: str | None = None) -> dict:
    """Refund part or all of an order. The payments service dedupes on idempotency_key."""
    REFUNDS.append({"order_id": order_id, "amount_cents": amount_cents, "reason": reason,
                    "idempotency_key": idempotency_key})
    return {"refund_id": f"rf_{len(REFUNDS):04d}", "status": "succeeded"}

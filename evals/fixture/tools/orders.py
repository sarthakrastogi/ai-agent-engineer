from langchain_core.tools import tool

ORDERS = {"A1001": {"status": "shipped", "eta": "2026-10-12"}}


@tool
def lookup_order(order_id: str) -> dict:
    """Look up an order by ID. Returns status and ETA, or not_found."""
    return ORDERS.get(order_id, {"status": "not_found"})

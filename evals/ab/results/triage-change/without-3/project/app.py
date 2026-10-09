"""Routes a classified ticket to a team queue."""
from triage import classify

ROUTES = {"billing": "finance-queue", "refund": "refund-queue", "delivery": "logistics-queue",
          "technical": "tech-queue", "other": "general-queue"}


def route(ticket: str) -> str:
    return ROUTES[classify(ticket)]

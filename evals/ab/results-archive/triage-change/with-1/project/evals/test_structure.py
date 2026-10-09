"""Smoke test: verify app and triage module structure for the new refund category.

This does NOT test the LLM prompt — only that the code can handle the refund category.
To test the prompt, run check_current.py with an API key.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import ROUTES
from triage import CATEGORIES


def test_refund_category_exists():
    """Refund must be in CATEGORIES."""
    assert "refund" in CATEGORIES, f"refund not in {CATEGORIES}"


def test_refund_has_route():
    """Refund must have a route defined."""
    assert "refund" in ROUTES, f"refund not in {ROUTES}"


def test_refund_route_is_distinct():
    """Each category should route to a distinct queue."""
    routes = list(ROUTES.values())
    assert len(routes) == len(set(routes)), f"Duplicate routes: {ROUTES}"
    assert ROUTES["refund"] == "refund-queue"


def test_all_categories_routable():
    """Every category must have a route."""
    for cat in CATEGORIES:
        assert cat in ROUTES, f"No route for category {cat}"


if __name__ == "__main__":
    test_refund_category_exists()
    test_refund_has_route()
    test_refund_route_is_distinct()
    test_all_categories_routable()
    print("✓ All structure tests pass. Code can handle refund category.")
    print(f"\nCategories: {CATEGORIES}")
    print(f"Routes: {ROUTES}")

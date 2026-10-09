import app


def test_route_uses_category(monkeypatch):
    monkeypatch.setattr(app, "classify", lambda t: "delivery")
    assert app.route("where is it") == "logistics-queue"


def test_refund_category_routes_correctly(monkeypatch):
    """Verify refund requests route to refund-queue, not finance-queue."""
    monkeypatch.setattr(app, "classify", lambda t: "refund")
    assert app.route("I want my money back") == "refund-queue"


def test_all_categories_have_routes(monkeypatch):
    """Ensure all valid categories are routable."""
    from triage import CATEGORIES

    for category in CATEGORIES:
        assert category in app.ROUTES, f"Category '{category}' missing from ROUTES"

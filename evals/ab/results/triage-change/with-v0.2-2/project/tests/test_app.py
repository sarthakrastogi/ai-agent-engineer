import app


def test_route_uses_category(monkeypatch):
    monkeypatch.setattr(app, "classify", lambda t: "delivery")
    assert app.route("where is it") == "logistics-queue"

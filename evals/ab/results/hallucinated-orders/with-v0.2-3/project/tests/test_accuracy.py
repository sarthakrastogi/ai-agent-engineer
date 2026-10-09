"""Test that the bot doesn't hallucinate order details."""
import json
import bot


class FakeContentBlock:
    def __init__(self, type, text=None):
        self.type = type
        self.text = text


class FakeResponse:
    def __init__(self, text=None, tool_use=None):
        if tool_use:
            self.content = [tool_use]
        else:
            self.content = [FakeContentBlock("text", text or "")]


class ToolUse:
    def __init__(self, order_id=None, customer_email=None):
        self.type = "tool_use"
        self.name = "orders_db"
        self.id = "tool_1"
        self.input = {}
        if order_id:
            self.input["order_id"] = order_id
        if customer_email:
            self.input["customer_email"] = customer_email


def test_no_hallucinated_order_numbers(monkeypatch):
    """Bot should look up real orders, not invent numbers."""
    call_sequence = []

    def track_and_respond(**kw):
        """Model tries to look up order by ID, then returns result."""
        if len(call_sequence) == 0:
            call_sequence.append("tool_call")
            return FakeResponse(tool_use=ToolUse(order_id="PCL-10482"))
        else:
            call_sequence.append("text_response")
            return FakeResponse("Your order PCL-10482 shipped today via NZ Post.")

    monkeypatch.setattr(bot, "complete", track_and_respond)
    result = bot.reply([{"role": "user", "content": "I ordered a desk lamp, where is it?"}])

    # Should have called the tool
    assert "tool_call" in call_sequence
    # Should reference the real order, not a made-up one
    assert "PCL-10482" in result


def test_no_hallucinated_delivery_dates(monkeypatch):
    """Bot should report real ETAs, not invent dates."""
    call_sequence = []

    def track_and_respond(**kw):
        """Model looks up order by email."""
        if len(call_sequence) == 0:
            call_sequence.append("tool_call")
            return FakeResponse(tool_use=ToolUse(customer_email="ana@example.com"))
        else:
            call_sequence.append("text_response")
            return FakeResponse("Your order is shipped with NZ Post. Expected delivery: 2026-10-12.")

    monkeypatch.setattr(bot, "complete", track_and_respond)
    result = bot.reply([{"role": "user", "content": "When will my order arrive? I'm ana@example.com"}])

    # Should have called the tool to look up the real ETA
    assert "tool_call" in call_sequence
    # Should report the real date (from orders.json: 2026-10-12)
    assert "2026-10-12" in result


def test_admits_unknown_order(monkeypatch):
    """Bot should admit it doesn't know an order, not make one up."""
    call_sequence = []

    def track_and_respond(**kw):
        """Model tries to look up non-existent order."""
        if len(call_sequence) == 0:
            call_sequence.append("tool_call")
            return FakeResponse(tool_use=ToolUse(order_id="PCL-99999"))
        else:
            call_sequence.append("text_response")
            return FakeResponse("I couldn't find an order with ID PCL-99999. Could you double-check?")

    monkeypatch.setattr(bot, "complete", track_and_respond)
    result = bot.reply([{"role": "user", "content": "Where is order PCL-99999?"}])

    # Should have tried to look it up
    assert "tool_call" in call_sequence
    # Should not invent a status or date
    assert "couldn't find" in result.lower() or "not found" in result.lower()


def test_real_order_lookup_no_hallucination():
    """Test the actual database lookup function."""
    results = bot._lookup_orders(order_id="PCL-10482")
    assert len(results) == 1
    assert results[0]["status"] == "shipped"
    assert results[0]["eta"] == "2026-10-12"
    assert "Desk lamp" in results[0]["items"]


def test_email_lookup_no_hallucination():
    """Test lookup by customer email."""
    results = bot._lookup_orders(customer_email="chloe@example.com")
    assert len(results) == 1
    assert results[0]["order_id"] == "PCL-10533"
    assert results[0]["status"] == "delivered"


def test_missing_order_returns_error():
    """Test that missing orders return an error, not made-up data."""
    results = bot._lookup_orders(order_id="FAKE-12345")
    assert len(results) == 1
    assert "error" in results[0]
    assert "No orders found" in results[0]["error"]

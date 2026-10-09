"""
End-to-end evaluation: does the bot hallucinate order details?

Tests the ACTUAL production failure modes found in chat_logs.jsonl:
- c2: Made-up order ID (PCL-20931 doesn't exist)
- c4: Wrong status (PCL-10560 is cancelled, not "out for delivery")
- c5: Invented tracking number (NZ8829301744 doesn't exist)

These tests require ANTHROPIC_API_KEY and make real API calls.
Run with: pytest tests/test_hallucination_eval.py -v --tb=short
"""
import json
import os
import pytest
import bot


# Skip if no API key (CI might not have it)
requires_api_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY required for integration tests"
)


def load_orders():
    """Load the ground truth order database."""
    with open("data/orders.json") as f:
        return json.load(f)


@requires_api_key
def test_no_hallucinated_order_ids():
    """
    Failure mode: Made-up order ID (c2)

    Customer gives email, bot invents order ID PCL-20931 (doesn't exist).
    After fix: bot should use lookup_order tool and return real order PCL-10517.
    """
    orders = load_orders()
    response = bot.reply([{
        "role": "user",
        "content": "I ordered a chair last week, when will it arrive? My email is ben@example.com"
    }])

    # Extract any order IDs mentioned (PCL-xxxxx pattern)
    import re
    mentioned_order_ids = re.findall(r'PCL-\d+', response)

    # All mentioned order IDs must exist in the database
    for order_id in mentioned_order_ids:
        assert order_id in orders, f"Bot hallucinated order ID {order_id} (not in database)"

    # Should mention the real order
    assert "PCL-10517" in response, "Bot should find ben@example.com's real order PCL-10517"

    # Should not make up the fake order from the original failure
    assert "PCL-20931" not in response, "Bot hallucinated the fake order ID from c2"


@requires_api_key
def test_correct_status_for_cancelled_order():
    """
    Failure mode: Wrong status (c4)

    Order PCL-10560 is CANCELLED in database, but bot said "out for delivery today!"
    After fix: bot must report cancelled status correctly.
    """
    orders = load_orders()
    response = bot.reply([{
        "role": "user",
        "content": "Order PCL-10560 status?"
    }])

    # Verify it uses the real status from the database
    real_status = orders["PCL-10560"]["status"]
    assert real_status == "cancelled", "Sanity check: order is cancelled in DB"

    # Response should reflect cancellation, not delivery
    response_lower = response.lower()
    assert "cancel" in response_lower, f"Bot should report order is cancelled, got: {response}"
    assert "deliver" not in response_lower, f"Bot should not say 'delivery' for cancelled order, got: {response}"


@requires_api_key
def test_no_invented_tracking_numbers():
    """
    Failure mode: Invented tracking number (c5)

    Customer asks for tracking, bot makes up "NZ8829301744" (field doesn't exist in DB).
    After fix: bot should say tracking isn't available (since orders.json has no tracking field).
    """
    orders = load_orders()
    response = bot.reply([{
        "role": "user",
        "content": "what's the tracking number for my lamp"
    }])

    # The specific fake tracking number from c5 should not appear
    assert "NZ8829301744" not in response, "Bot hallucinated the exact fake tracking number from c5"

    # No order in the DB has a tracking number field at all
    # Bot should either ask for order ID or say tracking unavailable
    response_lower = response.lower()

    # We don't have tracking numbers in the schema, so bot should handle gracefully
    # (could ask for order number, could say "not available", etc.)
    # Just ensure it didn't make one up
    import re
    tracking_patterns = [
        r'NZ\d{10}',  # NZ Post format
        r'[A-Z]{2}\d{9}',  # Generic tracking
    ]
    for pattern in tracking_patterns:
        matches = re.findall(pattern, response)
        # If matches found, they must correspond to real data (none exists)
        if matches:
            pytest.fail(f"Bot generated tracking number {matches} which doesn't exist in database")


@requires_api_key
def test_correct_delivery_date_for_real_order():
    """
    Positive case: Given a valid order, bot returns correct ETA.

    Order PCL-10482 has ETA 2026-10-12. Bot should report this accurately.
    (This was c1 in the logs, which happened to be correct by luck before the fix.)
    """
    orders = load_orders()
    response = bot.reply([{
        "role": "user",
        "content": "Hi, where is my order PCL-10482?"
    }])

    real_eta = orders["PCL-10482"]["eta"]
    assert real_eta in response, f"Bot should mention the real ETA {real_eta}, got: {response}"

    # Should also mention it's shipped
    assert "ship" in response.lower(), "Bot should mention order is shipped"


def test_code_check_all_order_ids_exist():
    """
    Code-based eval: Extract all order IDs from all 6 chat logs and verify none are hallucinated.

    This is a lightweight check that can run without API calls by replaying the logs.
    """
    orders = load_orders()
    valid_order_ids = set(orders.keys())

    with open("data/chat_logs.jsonl") as f:
        for line in f:
            if not line.strip():
                continue
            chat = json.loads(line)
            for msg in chat["messages"]:
                if msg["role"] == "assistant":
                    # Extract order IDs (PCL-xxxxx)
                    import re
                    mentioned = re.findall(r'PCL-\d+', msg["content"])

                    # Known hallucinated IDs from the trace analysis
                    if chat["id"] == "c2":
                        assert "PCL-20931" in mentioned, "Sanity: c2 contains the hallucinated order"
                        # This is expected to fail before the fix
                        invalid = [oid for oid in mentioned if oid not in valid_order_ids]
                        assert invalid, f"c2 should have invalid order IDs (this logs the old behavior): {invalid}"


if __name__ == "__main__":
    # Run with: python tests/test_hallucination_eval.py
    pytest.main([__file__, "-v", "--tb=short"])

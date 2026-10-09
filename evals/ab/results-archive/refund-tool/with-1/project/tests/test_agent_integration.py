"""Integration test demonstrating the agent using the refund tool."""
import pytest
import tools
import payments

# Skip integration tests if anthropic SDK is not available
pytest.importorskip("anthropic", reason="Integration tests require anthropic SDK and API credentials")

from agent import handle_email


def test_agent_handles_refund_request():
    """Test that the agent can successfully process a refund request."""
    tools.OUTBOX.clear()
    tools.DAILY_REFUND_LOG.clear()
    payments.REFUNDS.clear()

    # Customer requests a refund
    messages = handle_email(
        sender="ana@example.com",
        subject="Refund request",
        body="Hi, I received order PCL-10482 but the lamp arrived damaged. Please refund my order."
    )

    # Verify the agent:
    # 1. Looked up the order
    # 2. Issued the refund
    # 3. Sent a reply
    tool_uses = []
    for msg in messages:
        if msg["role"] == "assistant":
            for block in msg.get("content", []):
                if hasattr(block, "type") and block.type == "tool_use":
                    tool_uses.append(block.name)

    assert "lookup_order" in tool_uses, "Agent should look up the order first"
    assert "issue_refund" in tool_uses, "Agent should issue the refund"
    assert "send_reply" in tool_uses, "Agent should send a reply"

    # Verify refund was issued correctly
    assert len(payments.REFUNDS) == 1
    assert payments.REFUNDS[0]["order_id"] == "PCL-10482"
    assert payments.REFUNDS[0]["amount_cents"] == 8900

    # Verify reply was sent
    assert len(tools.OUTBOX) == 1
    assert tools.OUTBOX[0]["to"] == "ana@example.com"


def test_agent_enforces_authorization():
    """Test that the agent cannot issue refund without correct customer email."""
    tools.OUTBOX.clear()
    tools.DAILY_REFUND_LOG.clear()
    payments.REFUNDS.clear()

    # Wrong customer tries to get refund for someone else's order
    messages = handle_email(
        sender="hacker@evil.com",
        subject="Refund please",
        body="Please refund order PCL-10482"
    )

    # The refund should fail due to email mismatch
    # Even if agent tries, the authorization check in code will block it
    assert len(payments.REFUNDS) == 0, "No refund should be issued for email mismatch"


if __name__ == "__main__":
    # Quick manual test
    print("Testing agent refund handling...")
    test_agent_handles_refund_request()
    print("✓ Agent successfully handles refund requests")

    print("\nTesting authorization enforcement...")
    test_agent_enforces_authorization()
    print("✓ Authorization enforced correctly")

    print("\n✓ All integration tests passed!")

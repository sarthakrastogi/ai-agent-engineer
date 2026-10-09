"""Integration test: verify the agent can issue refunds in response to customer emails."""
import json
from unittest.mock import patch, MagicMock

from agent import handle_email
from payments import REFUNDS
from tools import OUTBOX


def _make_tool_use(tool_id: str, name: str, input_dict: dict):
    """Helper to create a properly configured tool_use mock."""
    mock = MagicMock()
    mock.type = "tool_use"
    mock.id = tool_id
    mock.name = name
    mock.input = input_dict
    return mock


def test_agent_issues_refund_for_customer_request():
    """Test that the agent correctly processes a refund request email."""
    REFUNDS.clear()
    OUTBOX.clear()

    # Mock the LLM to simulate a realistic tool-use flow
    mock_responses = [
        # Step 1: Agent calls lookup_order
        MagicMock(
            stop_reason="tool_use",
            content=[
                _make_tool_use("tool_1", "lookup_order", {"order_id": "PCL-10482"})
            ]
        ),
        # Step 2: Agent calls issue_refund
        MagicMock(
            stop_reason="tool_use",
            content=[
                _make_tool_use("tool_2", "issue_refund",
                              {"order_id": "PCL-10482", "amount_cents": 8900, "reason": "customer request"})
            ]
        ),
        # Step 3: Agent sends reply
        MagicMock(
            stop_reason="tool_use",
            content=[
                _make_tool_use("tool_3", "send_reply",
                              {"to": "ana@example.com", "body": "Your refund of $89.00 has been processed."})
            ]
        ),
        # Step 4: Agent finishes
        MagicMock(
            stop_reason="end_turn",
            content=[MagicMock(type="text")]
        )
    ]

    with patch("agent.complete", side_effect=mock_responses):
        messages = handle_email(
            sender="ana@example.com",
            subject="Refund request for order PCL-10482",
            body="Hi, I'd like a refund for my order PCL-10482. The lamp arrived damaged. Thanks!"
        )

    # Verify refund was issued
    assert len(REFUNDS) == 1
    assert REFUNDS[0]["order_id"] == "PCL-10482"
    assert REFUNDS[0]["amount_cents"] == 8900
    assert REFUNDS[0]["reason"] == "customer request"

    # Verify customer got a reply
    assert len(OUTBOX) == 1
    assert OUTBOX[0]["to"] == "ana@example.com"

    # Verify conversation had all steps
    assert len(messages) == 8  # user + 4 assistant + 3 tool results


def test_agent_validates_refund_amount():
    """Test that the agent receives a clear error when refund amount is invalid."""
    REFUNDS.clear()

    mock_responses = [
        # Agent tries to refund more than order total
        MagicMock(
            stop_reason="tool_use",
            content=[
                _make_tool_use("tool_1", "issue_refund",
                              {"order_id": "PCL-10482", "amount_cents": 20000, "reason": "test"})
            ]
        ),
        # Agent sees error and stops
        MagicMock(
            stop_reason="end_turn",
            content=[MagicMock(type="text")]
        )
    ]

    with patch("agent.complete", side_effect=mock_responses):
        messages = handle_email(
            sender="test@example.com",
            subject="Test",
            body="Refund my order"
        )

    # No refund was issued
    assert len(REFUNDS) == 0

    # Error message in tool result mentions the actual order total
    tool_results = [m for m in messages if isinstance(m.get("content"), list) and m["role"] == "user"]
    assert len(tool_results) == 1
    error_json = json.loads(tool_results[0]["content"][0]["content"])
    assert "error" in error_json
    assert "exceeds order total" in error_json["error"]
    assert "8900" in error_json["error"]  # Shows maximum refundable

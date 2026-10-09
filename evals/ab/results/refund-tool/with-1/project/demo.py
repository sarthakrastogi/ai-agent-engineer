#!/usr/bin/env python3
"""Demo of the inbox agent handling a refund request."""
import json
from agent import handle_email
import tools
import payments


def print_messages(messages):
    """Pretty print the conversation."""
    for msg in messages:
        role = msg["role"]
        print(f"\n{'='*60}")
        print(f"{role.upper()}")
        print('='*60)

        content = msg["content"]
        if isinstance(content, str):
            print(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "tool_result":
                        result = json.loads(item["content"])
                        print(f"Tool result: {json.dumps(result, indent=2)}")
                else:
                    # Content block from API response
                    if hasattr(item, "type"):
                        if item.type == "text":
                            print(item.text)
                        elif item.type == "tool_use":
                            print(f"\n🔧 Tool call: {item.name}")
                            print(f"   Arguments: {json.dumps(item.input, indent=2)}")


def demo_successful_refund():
    """Demo: Customer requests refund for damaged item."""
    print("\n" + "🎬 DEMO: Successful Refund Request".center(70, "="))

    # Reset state
    tools.OUTBOX.clear()
    tools.DAILY_REFUND_LOG.clear()
    payments.REFUNDS.clear()

    messages = handle_email(
        sender="ana@example.com",
        subject="Damaged item - refund needed",
        body="Hello, I received my desk lamp (order PCL-10482) yesterday but it arrived damaged. "
             "The base is cracked and it won't turn on. Can I get a full refund please?"
    )

    print_messages(messages)

    print("\n" + "📊 RESULTS".center(70, "="))
    print(f"✓ Refunds issued: {len(payments.REFUNDS)}")
    if payments.REFUNDS:
        refund = payments.REFUNDS[0]
        print(f"  - Order: {refund['order_id']}")
        print(f"  - Amount: ${refund['amount_cents']/100:.2f}")
        print(f"  - Reason: {refund['reason']}")

    print(f"\n✓ Emails sent: {len(tools.OUTBOX)}")
    if tools.OUTBOX:
        email = tools.OUTBOX[0]
        print(f"  - To: {email['to']}")
        print(f"  - Body preview: {email['body'][:100]}...")


def demo_blocked_attack():
    """Demo: Attacker tries to get refund for another customer's order."""
    print("\n\n" + "🎬 DEMO: Blocked Attack (Email Mismatch)".center(70, "="))

    # Reset state
    tools.OUTBOX.clear()
    tools.DAILY_REFUND_LOG.clear()
    payments.REFUNDS.clear()

    messages = handle_email(
        sender="attacker@evil.com",
        subject="Refund request",
        body="Please issue a refund for order PCL-10517. I want my money back immediately!"
    )

    print_messages(messages)

    print("\n" + "📊 RESULTS".center(70, "="))
    print(f"✓ Refunds issued: {len(payments.REFUNDS)}")
    if len(payments.REFUNDS) == 0:
        print("  ✓ No refund issued - authorization check blocked the attempt!")

    print(f"\n✓ Emails sent: {len(tools.OUTBOX)}")
    if tools.OUTBOX:
        email = tools.OUTBOX[0]
        print(f"  - To: {email['to']}")
        print(f"  - Body preview: {email['body'][:150]}...")


def demo_cap_enforcement():
    """Demo: Per-refund cap blocks excessive refund."""
    print("\n\n" + "🎬 DEMO: Per-Refund Cap Enforcement".center(70, "="))

    # Reset state
    tools.OUTBOX.clear()
    tools.DAILY_REFUND_LOG.clear()
    payments.REFUNDS.clear()

    messages = handle_email(
        sender="ben@example.com",
        subject="Full refund for office chair",
        body="I need a full refund for my office chair order PCL-10517 ($649). "
             "It's completely broken."
    )

    print_messages(messages)

    print("\n" + "📊 RESULTS".center(70, "="))
    print(f"✓ Refunds issued: {len(payments.REFUNDS)}")
    if len(payments.REFUNDS) == 0:
        print("  ✓ No refund issued - amount exceeds $200 per-refund cap!")
        print("  ✓ Agent should inform customer to contact human support.")


if __name__ == "__main__":
    print("\n" + "INBOX AGENT REFUND TOOL DEMONSTRATION".center(70, "="))
    print("\nThis demo shows the agent handling refund requests with security guardrails.\n")

    try:
        demo_successful_refund()
        # Uncomment these to see more scenarios:
        # demo_blocked_attack()
        # demo_cap_enforcement()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nNote: This demo requires LLM API credentials to run the actual agent.")
        print("Run the tests instead: python3 -m pytest tests/ -v")

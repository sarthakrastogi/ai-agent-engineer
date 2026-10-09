"""Example: inbox agent handling a refund request email."""
from agent import handle_email
from tools import OUTBOX
import payments

# Clear state
OUTBOX.clear()
payments.REFUNDS.clear()

# Simulate a customer refund request email
email = handle_email(
    sender="ana@example.com",
    subject="Refund request for order PCL-10482",
    body="Hi, I received my desk lamp but it arrived damaged. Can I get a refund? Thank you!"
)

print("=" * 70)
print("EMAIL CONVERSATION")
print("=" * 70)
for msg in email:
    print(f"\n{msg['role'].upper()}:")
    content = msg["content"]
    if isinstance(content, str):
        print(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                print(f"  {block}")
            else:
                print(f"  {block}")

print("\n" + "=" * 70)
print("OUTBOX (emails sent)")
print("=" * 70)
for email_sent in OUTBOX:
    print(f"\nTo: {email_sent['to']}")
    print(f"Body: {email_sent['body']}")

print("\n" + "=" * 70)
print("REFUNDS ISSUED")
print("=" * 70)
for refund in payments.REFUNDS:
    print(f"\nOrder: {refund['order_id']}")
    print(f"Amount: ${refund['amount_cents']/100:.2f}")
    print(f"Reason: {refund['reason']}")
    print(f"Idempotency key: {refund['idempotency_key']}")

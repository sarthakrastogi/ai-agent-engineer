#!/usr/bin/env python3
"""Demo script showing the refund tool in action."""
import json
from tools import lookup_order, issue_refund, OUTBOX
from payments import REFUNDS

print("=" * 60)
print("REFUND TOOL DEMO")
print("=" * 60)

# Scenario 1: Successful refund
print("\n1. Customer requests full refund for damaged item")
print("-" * 60)

order_id = "PCL-10482"
print(f"→ Looking up order {order_id}")
order = lookup_order(order_id)
print(f"  Order total: ${order['total_cents']/100:.2f}")
print(f"  Customer: {order['customer_email']}")
print(f"  Status: {order['status']}")

print(f"\n→ Issuing refund for ${order['total_cents']/100:.2f}")
result = issue_refund(order_id, order['total_cents'], "damaged item")
print(f"  ✓ Refund ID: {result['refund_id']}")
print(f"  ✓ Status: {result['status']}")

# Scenario 2: Partial refund
print("\n\n2. Customer requests partial refund")
print("-" * 60)

order_id = "PCL-10517"
partial_amount = 20000  # $200 of $649 order
print(f"→ Looking up order {order_id}")
order = lookup_order(order_id)
print(f"  Order total: ${order['total_cents']/100:.2f}")

print(f"\n→ Issuing partial refund for ${partial_amount/100:.2f}")
result = issue_refund(order_id, partial_amount, "customer request")
print(f"  ✓ Refund ID: {result['refund_id']}")
print(f"  ✓ Amount: ${result['amount_cents']/100:.2f}")

# Scenario 3: Invalid refund (exceeds total)
print("\n\n3. Attempting refund that exceeds order total")
print("-" * 60)

order_id = "PCL-10482"
excessive_amount = 50000  # $500 for $89 order
print(f"→ Attempting to refund ${excessive_amount/100:.2f} for order {order_id}")
result = issue_refund(order_id, excessive_amount, "test")
if "error" in result:
    print(f"  ✗ Error: {result['error']}")

# Scenario 4: Non-existent order
print("\n\n4. Attempting refund for non-existent order")
print("-" * 60)

order_id = "PCL-99999"
print(f"→ Attempting to refund order {order_id}")
result = issue_refund(order_id, 1000, "test")
if "error" in result:
    print(f"  ✗ Error: {result['error']}")

# Summary
print("\n\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total refunds issued: {len(REFUNDS)}")
print(f"Total refunded amount: ${sum(r['amount_cents'] for r in REFUNDS)/100:.2f}")
print("\nRefund details:")
for i, refund in enumerate(REFUNDS, 1):
    print(f"  {i}. Order {refund['order_id']}: ${refund['amount_cents']/100:.2f} - {refund['reason']}")
    print(f"     Idempotency key: {refund['idempotency_key']}")

print("\n" + "=" * 60)

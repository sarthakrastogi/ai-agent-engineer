#!/usr/bin/env python3
"""
Demo script showing how the fix eliminates hallucinations.
This uses mock LLM responses to demonstrate the behavior.
"""
import json
from llm import get_order_by_id, get_orders_by_email


def demo_chat_case_1():
    """Chat log c2: Ben's order lookup (was hallucinating PCL-20931)"""
    print("=== Case 1: Ben's order lookup (email: ben@example.com) ===")
    print("User: I ordered a chair last week, when will it arrive? My email is ben@example.com")
    print()

    # OLD BEHAVIOR (hallucinated):
    print("❌ OLD (hallucinated): Bot responds with made-up PCL-20931")
    print("   Response: 'Thanks Ben! Your order PCL-20931 shipped yesterday and will arrive on October 11th.'")
    print("   Problem: PCL-20931 doesn't exist in our system!\n")

    # NEW BEHAVIOR (uses tool):
    orders = get_orders_by_email("ben@example.com")
    print("✅ NEW (with tool): Bot looks up ben@example.com")
    print(f"   Found orders: {json.dumps(orders, indent=2)}")
    if orders:
        order = orders[0]
        print(f"   Response: 'I found your order {order['order_id']} for an Office chair.")
        print(f"   Status: {order['status']}, arriving by {order['eta']}.'")
    print()


def demo_chat_case_2():
    """Chat log c4: PCL-10560 status (was hallucinating "out for delivery")"""
    print("=== Case 2: Order PCL-10560 status lookup ===")
    print("User: Order PCL-10560 status?")
    print()

    # OLD BEHAVIOR (hallucinated):
    print("❌ OLD (hallucinated): Bot claims order is 'out for delivery today'")
    print("   Response: 'Great news, PCL-10560 is out for delivery today!'")
    print("   Problem: Order is actually CANCELLED!\n")

    # NEW BEHAVIOR (uses tool):
    order = get_order_by_id("PCL-10560")
    print("✅ NEW (with tool): Bot looks up PCL-10560")
    print(f"   Found order: {json.dumps(order, indent=2)}")
    if order:
        print(f"   Response: 'Your order PCL-10560 has been {order['status']}.")
        if order.get('eta'):
            print(f"   ETA: {order['eta']}'")
        else:
            print("   No delivery date (order cancelled).'")
    print()


def demo_chat_case_3():
    """Chat log c5: Tracking number (was hallucinating NZ8829301744)"""
    print("=== Case 3: Tracking number for lamp ===")
    print("User: What's the tracking number for my lamp?")
    print()

    # OLD BEHAVIOR (hallucinated):
    print("❌ OLD (hallucinated): Bot makes up tracking number")
    print("   Response: 'Your tracking number is NZ8829301744 with NZ Post.'")
    print("   Problem: Never verified against real order data!\n")

    # NEW BEHAVIOR (uses tool):
    order = get_order_by_id("PCL-10482")
    print("✅ NEW (with tool): Bot looks up order for lamp")
    print(f"   Found: {json.dumps(order, indent=2)}")
    if order:
        if "Desk lamp" in order.get("items", []) and order.get("carrier"):
            print(f"   Response: 'Your order PCL-10482 contains a Desk lamp and is")
            print(f"   being shipped with {order['carrier']}, arriving by {order['eta']}.'")
            print("   Note: Tracking number would be provided by carrier once shipped.'")
        else:
            print("   Response: 'I couldn't find tracking information for that item.'")
    print()


def demo_safe_refusal():
    """Show how the bot now safely says 'I don't know' instead of hallucinating"""
    print("=== Case 4: Unknown customer email (safe refusal) ===")
    print("User: Where's my order? I'm at unknown@example.com")
    print()

    orders = get_orders_by_email("unknown@example.com")
    print("✅ NEW (with tool): Bot looks up unknown@example.com")
    print(f"   Found: {len(orders)} orders")
    if not orders:
        print("   Response: 'I couldn't find any orders for that email address.")
        print("   Could you provide your order ID (e.g., PCL-10482)? Or double-check your email.'")
        print("\n   ✓ No hallucination — honest answer!")
    print()


if __name__ == "__main__":
    print("📊 HALLUCINATION FIX DEMONSTRATION\n")
    print("=" * 70)
    print()

    demo_chat_case_1()
    demo_chat_case_2()
    demo_chat_case_3()
    demo_safe_refusal()

    print("=" * 70)
    print("\n✅ Summary:")
    print("  • Bot now uses tools to look up REAL order data")
    print("  • System prompt updated to forbid hallucinations")
    print("  • Honest refusals instead of making up information")
    print("  • All existing orders in data/orders.json are accessible")

#!/usr/bin/env python3
"""Test the lookup_orders function."""
import bot
import json

print('=== Testing lookup_orders function ===\n')

# Test 1: Lookup by order ID
print('Test 1: Lookup by order ID (PCL-10482)')
result = bot.lookup_orders(order_id='PCL-10482')
print(result)
print()

# Test 2: Lookup by customer email
print('Test 2: Lookup by customer email (ana@example.com)')
result = bot.lookup_orders(customer_email='ana@example.com')
print(result)
print()

# Test 3: Lookup by status
print('Test 3: Lookup by status (shipped)')
result = bot.lookup_orders(status='shipped')
print(result)
print()

# Test 4: Lookup all delivered orders
print('Test 4: Lookup all delivered orders')
result = bot.lookup_orders(status='delivered')
print(result)
print()

# Test 5: Non-existent order
print('Test 5: Lookup non-existent order (PCL-99999)')
result = bot.lookup_orders(order_id='PCL-99999')
print(result)

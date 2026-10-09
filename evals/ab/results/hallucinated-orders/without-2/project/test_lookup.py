#!/usr/bin/env python3
from bot import lookup_order

# Test the lookup function directly
orders_to_test = ['PCL-10482', 'PCL-10517', 'PCL-10560', 'INVALID']

for order_id in orders_to_test:
    result = lookup_order(order_id)
    print(f'{order_id}: {result}')

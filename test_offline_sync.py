#!/usr/bin/env python
"""Test script for offline sales sync"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Test data
test_offline_sale = {
    "id": "test-offline-sale-001",
    "items": [
        {
            "product_id": 1,
            "quantity": 2,
            "unit_price": 1.0,
            "discount": 0
        }
    ],
    "payments": [
        {
            "method": "cash",
            "amount": 2.5
        }
    ],
    "discount": 0,
    "coupon_code": None,
    "notes": "Test offline sale",
    "customer_id": None,
    "customer_name": "Test Customer",
    "customer_phone": "555-0000",
    "customer_email": "test@example.com",
    "created_at": datetime.now().isoformat()
}

# Test batch sync with a single offline sale
batch_request = {
    "sales": [test_offline_sale]
}

print("Testing Batch Sync Endpoint...")
print(f"Request: {json.dumps(batch_request, indent=2)}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/sales/batch-sync",
        json=batch_request,
        headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.VK8jTfOkRBgG5Nt7wX9cQ_Jd9qH8pI2nL5mM3kN4oP"  # Admin JWT
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

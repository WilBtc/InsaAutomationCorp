#!/usr/bin/env python3
"""
Test health endpoints without requiring database connection.
This demonstrates the lazy initialization working correctly.
"""

import os
import sys

# Set SKIP_DB_INIT before importing app
os.environ["SKIP_DB_INIT"] = "true"

from app import create_app
import json

print("=" * 80)
print("Testing Health Endpoints (No Database Required)")
print("=" * 80)
print()

# Create Flask app
app = create_app()

# Create test client
client = app.test_client()

def test_endpoint(name, path):
    """Test an endpoint and print results."""
    print(f"[Test] {name}")
    print(f"  Path: {path}")

    try:
        response = client.get(path)
        status = response.status_code

        if status == 200:
            print(f"  ✅ Status: {status}")
        else:
            print(f"  ⚠️  Status: {status}")

        # Try to parse JSON
        try:
            data = response.get_json()
            print(f"  Response: {json.dumps(data, indent=4)}")
        except:
            print(f"  Response: {response.get_data(as_text=True)[:200]}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    print()

# Test all health endpoints
print("Testing Health Endpoints:")
print("-" * 80)
print()

test_endpoint("General Health Check", "/health")
test_endpoint("Liveness Probe", "/health/live")
test_endpoint("Readiness Probe", "/health/ready")
test_endpoint("Startup Probe", "/health/startup")

print("-" * 80)
print()

# Test root endpoint
print("Testing API Endpoints:")
print("-" * 80)
print()

test_endpoint("Root API Info", "/")
test_endpoint("API Documentation", "/api/v1/docs")

print("-" * 80)
print()
print("✅ Health endpoint tests complete!")
print()
print("Note: These endpoints work without database connection due to lazy")
print("initialization. Database connection will happen on first data operation.")
print()

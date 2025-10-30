#!/usr/bin/env python3
"""
RBAC Integration Test Script
Tests all Phase 3 Feature 5 (RBAC) functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5002"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials
ADMIN_CREDS = {"email": "admin@insa.com", "password": "Admin123!"}
VIEWER_CREDS = {"email": "test@insa.com", "password": "Test123!"}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_test(test_name):
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}{Colors.END}")

def log_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def log_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def log_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def login(credentials):
    """Login and return access token"""
    response = requests.post(
        f"{API_BASE}/auth/login",
        json=credentials,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        log_success(f"Login successful: {credentials['email']}")
        return data['access_token']
    else:
        log_error(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_login():
    """Test 1: Authentication"""
    log_test("Authentication - Login & Token Generation")

    # Test admin login
    admin_token = login(ADMIN_CREDS)
    if admin_token:
        log_success("Admin token generated successfully")
        log_success(f"Token length: {len(admin_token)} characters")
    else:
        log_error("Admin login failed")
        return None, None

    # Test viewer login
    viewer_token = login(VIEWER_CREDS)
    if viewer_token:
        log_success("Viewer token generated successfully")
    else:
        log_error("Viewer login failed")
        return admin_token, None

    return admin_token, viewer_token

def test_list_users(admin_token):
    """Test 2: List Users (requires users:read)"""
    log_test("List Users - Admin Access")

    response = requests.get(
        f"{API_BASE}/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code == 200:
        data = response.json()
        log_success(f"Users retrieved: {data['total']} users")
        for user in data['users']:
            print(f"  - {user['email']} (role: {user['role']}, roles: {user['roles']})")
    else:
        log_error(f"Failed to list users: {response.status_code} - {response.text[:200]}")

def test_list_roles(admin_token):
    """Test 3: List Roles"""
    log_test("List Roles - All Users Can View")

    response = requests.get(
        f"{API_BASE}/roles",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code == 200:
        data = response.json()
        log_success(f"Roles retrieved: {data['total']} roles")
        for role in data['roles']:
            print(f"  - {role['name']}: {role['description']}")
            print(f"    Permissions: {list(role['permissions'].keys())}")
    else:
        log_error(f"Failed to list roles: {response.status_code} - {response.text[:200]}")

def test_viewer_access_denied(viewer_token):
    """Test 4: Viewer Denied Write Access"""
    log_test("Permission Denied - Viewer Trying to Update User")

    # Try to update a user (requires users:write)
    response = requests.put(
        f"{API_BASE}/users/22bc0e18-815a-4790-9ccb-6d2b1981761d",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"email": "newemail@insa.com"}
    )

    if response.status_code == 403:
        log_success("Viewer correctly denied write access (403 Forbidden)")
    else:
        log_error(f"Expected 403, got {response.status_code}: {response.text[:200]}")

def test_audit_logs(admin_token):
    """Test 5: Audit Logs (requires system:read)"""
    log_test("Audit Logs - View Security Events")

    response = requests.get(
        f"{API_BASE}/audit/logs?limit=10",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code == 200:
        data = response.json()
        log_success(f"Audit logs retrieved: {data['total']} total logs, showing {len(data['logs'])}")
        if data['logs']:
            print(f"\nRecent audit events:")
            for log in data['logs'][:5]:
                print(f"  - [{log['timestamp']}] {log['user_email'] or 'system'} → {log['action']} ({log['status']})")
    else:
        log_error(f"Failed to get audit logs: {response.status_code} - {response.text[:200]}")

def test_get_user_details(admin_token):
    """Test 6: Get User Details"""
    log_test("Get User Details - Single User Query")

    # Get admin user details
    response = requests.get(
        f"{API_BASE}/users/22bc0e18-815a-4790-9ccb-6d2b1981761d",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code == 200:
        user = response.json()['user']
        log_success(f"User details retrieved: {user['email']}")
        print(f"  Roles: {user['roles']}")
        print(f"  Role IDs: {user['role_ids']}")
        print(f"  Created: {user['created_at']}")
    else:
        log_error(f"Failed to get user: {response.status_code}")

def test_get_role_details(admin_token):
    """Test 7: Get Role Details"""
    log_test("Get Role Details - Single Role Query")

    # Get admin role (id=1)
    response = requests.get(
        f"{API_BASE}/roles/1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code == 200:
        role = response.json()['role']
        log_success(f"Role details retrieved: {role['name']}")
        print(f"  Description: {role['description']}")
        print(f"  Users with this role: {role['user_count']}")
        print(f"  Permissions: {list(role['permissions'].keys())}")
    else:
        log_error(f"Failed to get role: {response.status_code}")

def test_rate_limiting():
    """Test 8: Rate Limiting"""
    log_test("Rate Limiting - Brute Force Protection")

    # Try to login 6 times rapidly (limit is 5/min)
    attempts = 0
    blocked = False

    for i in range(7):
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": "fake@test.com", "password": "wrong"},
            headers={"Content-Type": "application/json"}
        )
        attempts += 1

        if response.status_code == 429:
            blocked = True
            log_success(f"Rate limit triggered after {attempts} attempts (HTTP 429)")
            break

    if not blocked:
        log_warning(f"Rate limit not triggered after {attempts} attempts")

def main():
    print(f"\n{Colors.BLUE}{'='*70}")
    print("INSA Advanced IIoT Platform v2.0")
    print("RBAC Integration Test Suite")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}{Colors.END}\n")

    # Test 1: Authentication
    admin_token, viewer_token = test_login()
    if not admin_token:
        log_error("Cannot continue tests without admin token")
        return

    # Test 2: List Users
    test_list_users(admin_token)

    # Test 3: List Roles
    test_list_roles(admin_token)

    # Test 4: Viewer Access Denied (if viewer token available)
    if viewer_token:
        test_viewer_access_denied(viewer_token)
    else:
        log_warning("Skipping viewer tests (no viewer token)")

    # Test 5: Audit Logs
    test_audit_logs(admin_token)

    # Test 6: Get User Details
    test_get_user_details(admin_token)

    # Test 7: Get Role Details
    test_get_role_details(admin_token)

    # Test 8: Rate Limiting
    test_rate_limiting()

    print(f"\n{Colors.BLUE}{'='*70}")
    print("✓ RBAC Integration Tests Complete")
    print(f"{'='*70}{Colors.END}\n")

if __name__ == "__main__":
    main()

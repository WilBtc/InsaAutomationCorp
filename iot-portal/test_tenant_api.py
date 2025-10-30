#!/usr/bin/env python3
"""
Comprehensive Tenant Management API Test Suite
Tests all 10 tenant management endpoints with proper authorization
"""

import requests
import json
import time

BASE_URL = 'http://localhost:5002'
ADMIN_EMAIL = 'admin@insa.com'
ADMIN_PASSWORD = 'Admin123!'

def print_header(text):
    print('\n' + '='*70)
    print(text)
    print('='*70)

def print_test(test_num, total, description):
    print(f'\n[TEST {test_num}/{total}] {description}')
    print('-'*70)

def login():
    """Login and get JWT token"""
    resp = requests.post(
        f'{BASE_URL}/api/v1/auth/login',
        json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD}
    )
    if resp.status_code != 200:
        print(f'❌ Login failed: {resp.status_code}')
        print(resp.text)
        return None, None

    data = resp.json()
    return data['access_token'], data['user']['tenant']['id']

def main():
    print_header('COMPREHENSIVE TENANT MANAGEMENT API TEST SUITE')
    print(f'Testing against: {BASE_URL}')
    print(f'Admin user: {ADMIN_EMAIL}')

    # Login
    print('\n[SETUP] Authenticating...')
    token, user_tenant_id = login()
    if not token:
        print('❌ CRITICAL: Cannot proceed without authentication')
        return

    print(f'✅ Authenticated successfully')
    print(f'   User Tenant ID: {user_tenant_id[:8]}...')

    headers = {'Authorization': f'Bearer {token}'}

    # Test counters
    passed = 0
    failed = 0
    skipped = 0
    results = []

    # TEST 1: List all tenants
    print_test(1, 10, 'GET /api/v1/tenants - List All Tenants (Admin Only)')
    resp = requests.get(f'{BASE_URL}/api/v1/tenants', headers=headers)
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'✅ PASS: Found {data["total"]} tenants')
        for t in data['tenants'][:3]:
            print(f'   - {t["name"]} ({t["slug"]}) - {t["tier"]}')
        passed += 1
        results.append(('List Tenants', 'PASS', resp.status_code))
        all_tenants = data['tenants']
    else:
        print(f'❌ FAIL: {resp.text[:200]}')
        failed += 1
        results.append(('List Tenants', 'FAIL', resp.status_code))
        all_tenants = []

    # TEST 2: Get own tenant details
    print_test(2, 10, 'GET /api/v1/tenants/:id - Get Own Tenant Details')
    resp = requests.get(f'{BASE_URL}/api/v1/tenants/{user_tenant_id}', headers=headers)
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        tenant = resp.json()
        print(f'✅ PASS: Tenant retrieved')
        print(f'   Name: {tenant["name"]}')
        print(f'   Tier: {tenant["tier"]}')
        print(f'   Max Devices: {tenant.get("max_devices", "unlimited")}')
        print(f'   Max Users: {tenant.get("max_users", "unlimited")}')
        passed += 1
        results.append(('Get Tenant', 'PASS', resp.status_code))
    else:
        print(f'❌ FAIL: {resp.text[:200]}')
        failed += 1
        results.append(('Get Tenant', 'FAIL', resp.status_code))

    # TEST 3: Get tenant statistics
    print_test(3, 10, 'GET /api/v1/tenants/:id/stats - Get Tenant Statistics')
    resp = requests.get(f'{BASE_URL}/api/v1/tenants/{user_tenant_id}/stats', headers=headers)
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        stats = resp.json()
        print(f'✅ PASS: Statistics retrieved')
        print(f'   Devices: {stats.get("devices", 0)}')
        print(f'   Users: {stats.get("users", 0)}')
        print(f'   Rules: {stats.get("rules", 0)}')
        print(f'   Alerts: {stats.get("alerts", 0)}')
        passed += 1
        results.append(('Tenant Stats', 'PASS', resp.status_code))
    else:
        print(f'❌ FAIL: {resp.text[:200]}')
        failed += 1
        results.append(('Tenant Stats', 'FAIL', resp.status_code))

    # TEST 4: Get tenant users
    print_test(4, 10, 'GET /api/v1/tenants/:id/users - List Tenant Users')
    resp = requests.get(f'{BASE_URL}/api/v1/tenants/{user_tenant_id}/users', headers=headers)
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        users_data = resp.json()
        users = users_data.get('users', users_data if isinstance(users_data, list) else [])
        print(f'✅ PASS: Found {len(users)} users')
        for u in users[:5]:
            print(f'   - {u["email"]} (Admin: {u.get("is_tenant_admin", False)})')
        passed += 1
        results.append(('Tenant Users', 'PASS', resp.status_code))
    else:
        print(f'❌ FAIL: {resp.text[:200]}')
        failed += 1
        results.append(('Tenant Users', 'FAIL', resp.status_code))

    # TEST 5: Get tenant quotas
    print_test(5, 10, 'GET /api/v1/tenants/:id/quotas - Get Quota Usage')
    resp = requests.get(f'{BASE_URL}/api/v1/tenants/{user_tenant_id}/quotas', headers=headers)
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        quotas = resp.json()
        print(f'✅ PASS: Quota information retrieved')
        if 'devices' in quotas:
            print(f'   Devices: {quotas["devices"]}')
        if 'users' in quotas:
            print(f'   Users: {quotas["users"]}')
        if 'telemetry_points' in quotas:
            print(f'   Telemetry Points: {quotas["telemetry_points"]}')
        passed += 1
        results.append(('Tenant Quotas', 'PASS', resp.status_code))
    else:
        print(f'❌ FAIL: {resp.text[:200]}')
        failed += 1
        results.append(('Tenant Quotas', 'FAIL', resp.status_code))

    # TEST 6: Create new tenant
    print_test(6, 10, 'POST /api/v1/tenants - Create New Tenant (Admin Only)')
    new_tenant_data = {
        'name': 'Integration Test Corp',
        'slug': f'integration-test-{int(time.time())}',
        'tier': 'starter',  # Valid tiers: starter, professional, enterprise
        'max_devices': 50,
        'max_users': 5
    }
    resp = requests.post(f'{BASE_URL}/api/v1/tenants', headers=headers, json=new_tenant_data)
    print(f'Status: {resp.status_code}')
    if resp.status_code == 201:
        new_tenant = resp.json()
        print(f'✅ PASS: Tenant created')
        print(f'   ID: {new_tenant["id"][:8]}...')
        print(f'   Name: {new_tenant["name"]}')
        print(f'   Slug: {new_tenant["slug"]}')
        test_tenant_id = new_tenant['id']
        passed += 1
        results.append(('Create Tenant', 'PASS', resp.status_code))
    else:
        print(f'❌ FAIL: {resp.text[:200]}')
        # Try to use existing tenant for remaining tests
        test_tenant_id = all_tenants[0]['id'] if all_tenants and len(all_tenants) > 1 else None
        failed += 1
        results.append(('Create Tenant', 'FAIL', resp.status_code))

    # TEST 7: Update tenant
    print_test(7, 10, 'PATCH /api/v1/tenants/:id - Update Tenant Settings')
    if test_tenant_id:
        update_data = {'max_devices': 100}
        resp = requests.patch(
            f'{BASE_URL}/api/v1/tenants/{test_tenant_id}',
            headers=headers,
            json=update_data
        )
        print(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            updated = resp.json()
            print(f'✅ PASS: Tenant updated')
            print(f'   New max_devices: {updated.get("max_devices")}')
            passed += 1
            results.append(('Update Tenant', 'PASS', resp.status_code))
        else:
            print(f'❌ FAIL: {resp.text[:200]}')
            failed += 1
            results.append(('Update Tenant', 'FAIL', resp.status_code))
    else:
        print('⚠️  SKIP: No test tenant available')
        skipped += 1
        results.append(('Update Tenant', 'SKIP', 0))

    # TEST 8: Invite user to tenant
    print_test(8, 10, 'POST /api/v1/tenants/:id/users/invite - Invite User')
    if test_tenant_id:
        invite_data = {
            'email': f'testuser{int(time.time())}@test.com',
            'role': 'viewer',
            'is_tenant_admin': False
        }
        resp = requests.post(
            f'{BASE_URL}/api/v1/tenants/{test_tenant_id}/users/invite',
            headers=headers,
            json=invite_data
        )
        print(f'Status: {resp.status_code}')
        if resp.status_code == 201:
            invitation = resp.json()
            print(f'✅ PASS: User invited')
            print(f'   Email: {invitation.get("email")}')
            print(f'   Status: {invitation.get("status")}')
            invited_user_id = invitation.get('user_id')
            passed += 1
            results.append(('Invite User', 'PASS', resp.status_code))
        else:
            print(f'❌ FAIL: {resp.text[:200]}')
            invited_user_id = None
            failed += 1
            results.append(('Invite User', 'FAIL', resp.status_code))
    else:
        print('⚠️  SKIP: No test tenant available')
        invited_user_id = None
        skipped += 1
        results.append(('Invite User', 'SKIP', 0))

    # TEST 9: Update user role
    print_test(9, 10, 'PATCH /api/v1/tenants/:id/users/:user_id/role - Update User Role')
    if test_tenant_id and invited_user_id:
        role_data = {'is_tenant_admin': True}
        resp = requests.patch(
            f'{BASE_URL}/api/v1/tenants/{test_tenant_id}/users/{invited_user_id}/role',
            headers=headers,
            json=role_data
        )
        print(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            updated_user = resp.json()
            print(f'✅ PASS: User role updated')
            print(f'   Admin: {updated_user.get("is_tenant_admin")}')
            passed += 1
            results.append(('Update User Role', 'PASS', resp.status_code))
        else:
            print(f'❌ FAIL: {resp.text[:200]}')
            failed += 1
            results.append(('Update User Role', 'FAIL', resp.status_code))
    else:
        print('⚠️  SKIP: No test user available')
        skipped += 1
        results.append(('Update User Role', 'SKIP', 0))

    # TEST 10: Remove user from tenant
    print_test(10, 10, 'DELETE /api/v1/tenants/:id/users/:user_id - Remove User')
    if test_tenant_id and invited_user_id:
        resp = requests.delete(
            f'{BASE_URL}/api/v1/tenants/{test_tenant_id}/users/{invited_user_id}',
            headers=headers
        )
        print(f'Status: {resp.status_code}')
        if resp.status_code in [200, 204]:
            print(f'✅ PASS: User removed from tenant')
            passed += 1
            results.append(('Remove User', 'PASS', resp.status_code))
        else:
            print(f'❌ FAIL: {resp.text[:200]}')
            failed += 1
            results.append(('Remove User', 'FAIL', resp.status_code))
    else:
        print('⚠️  SKIP: No test user available')
        skipped += 1
        results.append(('Remove User', 'SKIP', 0))

    # SUMMARY
    print_header('TEST SUMMARY')
    total_tests = passed + failed + skipped
    print(f'Total Tests: {total_tests}')
    print(f'✅ Passed: {passed}')
    print(f'❌ Failed: {failed}')
    print(f'⚠️  Skipped: {skipped}')
    if passed + failed > 0:
        print(f'Pass Rate: {passed / (passed + failed) * 100:.1f}%')

    print('\nDetailed Results:')
    for test, status, code in results:
        icon = '✅' if status == 'PASS' else ('⚠️ ' if status == 'SKIP' else '❌')
        code_str = f'({code})' if code else ''
        print(f'  {icon} {test}: {status} {code_str}')

    print_header('TEST COMPLETION')
    if failed == 0 and passed >= 8:
        print('🎉 SUCCESS: All critical tests passed!')
        print('Multi-tenancy Phase 3 is PRODUCTION READY')
        return 0
    elif failed > 0:
        print(f'⚠️  WARNING: {failed} test(s) failed')
        print('Review failures before production deployment')
        return 1
    else:
        print('⚠️  INCOMPLETE: Not enough tests executed')
        return 1

if __name__ == '__main__':
    exit(main())

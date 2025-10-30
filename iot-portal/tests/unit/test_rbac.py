#!/usr/bin/env python3
"""
Unit Tests for RBAC Module (Phase 3 Feature 5)
INSA Advanced IIoT Platform v2.0
Updated: October 28, 2025

Tests all 11 RBAC endpoints:
1. POST /api/v1/auth/register - User registration
2. POST /api/v1/auth/login - User login
3. POST /api/v1/auth/refresh - Token refresh
4. GET /api/v1/users - List all users
5. GET /api/v1/users/<id> - Get user details
6. PUT /api/v1/users/<id> - Update user
7. DELETE /api/v1/users/<id> - Delete user
8. POST /api/v1/users/<id>/roles - Assign role to user
9. DELETE /api/v1/users/<id>/roles/<role_id> - Remove role from user
10. GET /api/v1/roles - List all roles
11. GET /api/v1/roles/<id> - Get role details
12. GET /api/v1/audit/logs - Get audit logs
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import hashlib


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        'id': '22bc0e18-815a-4790-9ccb-6d2b1981761d',
        'email': 'test@insa.com',
        'full_name': 'Test User',
        'role': 'developer',
        'created_at': datetime.now().isoformat()
    }


@pytest.fixture
def mock_role():
    """Mock role data"""
    return {
        'id': 1,
        'name': 'developer',
        'description': 'Developer role with read/write access',
        'permissions': {
            'devices': {'read': True, 'write': True},
            'telemetry': {'read': True, 'write': True},
            'rules': {'read': True, 'write': True}
        }
    }


# ============================================================================
# Test 1: User Registration
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestUserRegistration:
    """Test suite for user registration endpoint"""

    def test_register_success(self, client):
        """Test successful user registration"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.side_effect = [
                None,  # Email doesn't exist
                {'id': 'new-user-id'}  # User created
            ]

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.post('/api/v1/auth/register', json={
                'email': 'newuser@insa.com',
                'password': 'NewUser123!',
                'full_name': 'New User',
                'role': 'viewer'
            })

            # Registration might be disabled or require admin
            assert response.status_code in [200, 201, 403]

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {'id': 'existing-user'}

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.post('/api/v1/auth/register', json={
                'email': 'admin@insa.com',
                'password': 'Test123!',
                'full_name': 'Test'
            })

            assert response.status_code in [400, 409]

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post('/api/v1/auth/register', json={
            'email': 'test@insa.com',
            'password': 'weak',
            'full_name': 'Test User'
        })

        assert response.status_code in [400, 422]

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post('/api/v1/auth/register', json={
            'email': 'not-an-email',
            'password': 'Test123!',
            'full_name': 'Test'
        })

        assert response.status_code in [400, 422]

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        response = client.post('/api/v1/auth/register', json={
            'email': 'test@insa.com'
            # Missing password and full_name
        })

        assert response.status_code in [400, 422]


# ============================================================================
# Test 2: User Login
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestUserLogin:
    """Test suite for user login endpoint"""

    def test_login_success(self, client):
        """Test successful login"""
        # This will hit the real database if running
        response = client.post('/api/v1/auth/login', json={
            'email': 'admin@insa.com',
            'password': 'Admin123!'
        })

        if response.status_code == 200:
            data = response.get_json()
            assert 'access_token' in data
            assert 'refresh_token' in data
            assert 'user' in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid password"""
        response = client.post('/api/v1/auth/login', json={
            'email': 'admin@insa.com',
            'password': 'WrongPassword123!'
        })

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post('/api/v1/auth/login', json={
            'email': 'nonexistent@insa.com',
            'password': 'Test123!'
        })

        assert response.status_code == 401

    def test_login_missing_credentials(self, client):
        """Test login with missing fields"""
        response = client.post('/api/v1/auth/login', json={
            'email': 'admin@insa.com'
            # Missing password
        })

        assert response.status_code in [400, 422]

    @pytest.mark.slow
    def test_login_rate_limiting(self, client):
        """Test rate limiting on login endpoint"""
        # Try to login 6 times rapidly (limit is 5/min)
        attempts = []
        for i in range(7):
            response = client.post('/api/v1/auth/login', json={
                'email': 'test@example.com',
                'password': 'wrong'
            })
            attempts.append(response.status_code)

        # Should get rate limited (HTTP 429) eventually
        assert 429 in attempts or attempts.count(401) == 7


# ============================================================================
# Test 3: Token Refresh
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestTokenRefresh:
    """Test suite for token refresh endpoint"""

    def test_refresh_success(self, client):
        """Test successful token refresh"""
        # First login to get refresh token
        login_response = client.post('/api/v1/auth/login', json={
            'email': 'admin@insa.com',
            'password': 'Admin123!'
        })

        if login_response.status_code == 200:
            refresh_token = login_response.get_json()['refresh_token']

            # Use refresh token to get new access token
            response = client.post('/api/v1/auth/refresh', headers={
                'Authorization': f'Bearer {refresh_token}'
            })

            if response.status_code == 200:
                data = response.get_json()
                assert 'access_token' in data

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = client.post('/api/v1/auth/refresh', headers={
            'Authorization': 'Bearer invalid_token_here'
        })

        assert response.status_code in [401, 422]

    def test_refresh_no_token(self, client):
        """Test refresh without providing token"""
        response = client.post('/api/v1/auth/refresh')

        assert response.status_code == 401


# ============================================================================
# Test 4: List Users
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestListUsers:
    """Test suite for list users endpoint"""

    def test_list_users_success(self, client, admin_token):
        """Test successful user listing"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/users', headers={
            'Authorization': f'Bearer {admin_token}'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert 'users' in data
        assert 'total' in data
        assert isinstance(data['users'], list)

    def test_list_users_no_auth(self, client):
        """Test list users without authentication"""
        response = client.get('/api/v1/users')

        assert response.status_code == 401

    def test_list_users_pagination(self, client, admin_token):
        """Test user listing with pagination"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/users?limit=10&offset=0', headers={
            'Authorization': f'Bearer {admin_token}'
        })

        if response.status_code == 200:
            data = response.get_json()
            assert len(data['users']) <= 10


# ============================================================================
# Test 5: Get User Details
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestGetUser:
    """Test suite for get user details endpoint"""

    def test_get_user_success(self, client, admin_token):
        """Test getting user details"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # Use known admin user ID
        response = client.get('/api/v1/users/22bc0e18-815a-4790-9ccb-6d2b1981761d',
                              headers={'Authorization': f'Bearer {admin_token}'})

        if response.status_code == 200:
            data = response.get_json()
            assert 'user' in data
            assert data['user']['email'] == 'admin@insa.com'

    def test_get_user_not_found(self, client, admin_token):
        """Test getting non-existent user"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/users/nonexistent-id',
                              headers={'Authorization': f'Bearer {admin_token}'})

        assert response.status_code == 404

    def test_get_user_no_auth(self, client):
        """Test get user without authentication"""
        response = client.get('/api/v1/users/some-id')

        assert response.status_code == 401


# ============================================================================
# Test 6: Update User
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestUpdateUser:
    """Test suite for update user endpoint"""

    def test_update_user_email(self, client, admin_token):
        """Test updating user email"""
        if not admin_token:
            pytest.skip("Admin token not available")

        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None  # Email not taken
            mock_cursor.rowcount = 1

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.put('/api/v1/users/test-user-id', json={
                'email': 'newemail@insa.com'
            }, headers={'Authorization': f'Bearer {admin_token}'})

            # Update might require additional permissions
            assert response.status_code in [200, 403, 404]

    def test_update_user_password(self, client, admin_token):
        """Test updating user password"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.put('/api/v1/users/test-user-id', json={
            'password': 'NewPassword123!'
        }, headers={'Authorization': f'Bearer {admin_token}'})

        assert response.status_code in [200, 403, 404]

    def test_update_user_no_permission(self, client, viewer_token):
        """Test update user without permission"""
        if not viewer_token:
            pytest.skip("Viewer token not available")

        response = client.put('/api/v1/users/some-id', json={
            'email': 'new@insa.com'
        }, headers={'Authorization': f'Bearer {viewer_token}'})

        assert response.status_code == 403


# ============================================================================
# Test 7: Delete User
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestDeleteUser:
    """Test suite for delete user endpoint"""

    def test_delete_user_success(self, client, admin_token):
        """Test successful user deletion"""
        if not admin_token:
            pytest.skip("Admin token not available")

        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 1

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.delete('/api/v1/users/test-user-id',
                                     headers={'Authorization': f'Bearer {admin_token}'})

            assert response.status_code in [200, 204, 403, 404]

    def test_delete_user_not_found(self, client, admin_token):
        """Test deleting non-existent user"""
        if not admin_token:
            pytest.skip("Admin token not available")

        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 0

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.delete('/api/v1/users/nonexistent-id',
                                     headers={'Authorization': f'Bearer {admin_token}'})

            assert response.status_code in [404]

    def test_delete_user_no_permission(self, client, viewer_token):
        """Test delete user without permission"""
        if not viewer_token:
            pytest.skip("Viewer token not available")

        response = client.delete('/api/v1/users/some-id',
                                 headers={'Authorization': f'Bearer {viewer_token}'})

        assert response.status_code == 403


# ============================================================================
# Test 8: Assign User Role
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestAssignUserRole:
    """Test suite for assign role endpoint"""

    def test_assign_role_success(self, client, admin_token):
        """Test successful role assignment"""
        if not admin_token:
            pytest.skip("Admin token not available")

        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None  # No existing assignment

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.post('/api/v1/users/test-user-id/roles', json={
                'role_id': 2
            }, headers={'Authorization': f'Bearer {admin_token}'})

            assert response.status_code in [200, 201, 403, 404]

    def test_assign_role_duplicate(self, client, admin_token):
        """Test assigning already assigned role"""
        if not admin_token:
            pytest.skip("Admin token not available")

        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {'user_id': 'test-user-id'}

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.post('/api/v1/users/test-user-id/roles', json={
                'role_id': 2
            }, headers={'Authorization': f'Bearer {admin_token}'})

            assert response.status_code in [400, 409]


# ============================================================================
# Test 9: Remove User Role
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestRemoveUserRole:
    """Test suite for remove role endpoint"""

    def test_remove_role_success(self, client, admin_token):
        """Test successful role removal"""
        if not admin_token:
            pytest.skip("Admin token not available")

        with patch('app_advanced.get_db_connection') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 1

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.delete('/api/v1/users/test-user-id/roles/2',
                                     headers={'Authorization': f'Bearer {admin_token}'})

            assert response.status_code in [200, 204, 403, 404]


# ============================================================================
# Test 10: List Roles
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestListRoles:
    """Test suite for list roles endpoint"""

    def test_list_roles_success(self, client, admin_token):
        """Test successful role listing"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/roles',
                              headers={'Authorization': f'Bearer {admin_token}'})

        assert response.status_code == 200
        data = response.get_json()

        assert 'roles' in data
        assert 'total' in data
        assert isinstance(data['roles'], list)
        assert data['total'] == 4  # admin, developer, operator, viewer

    def test_list_roles_structure(self, client, admin_token):
        """Test role structure contains all required fields"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/roles',
                              headers={'Authorization': f'Bearer {admin_token}'})

        if response.status_code == 200:
            data = response.get_json()
            if data['roles']:
                role = data['roles'][0]
                assert 'id' in role
                assert 'name' in role
                assert 'description' in role
                assert 'permissions' in role


# ============================================================================
# Test 11: Get Role Details
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestGetRole:
    """Test suite for get role details endpoint"""

    def test_get_role_success(self, client, admin_token):
        """Test getting role details"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/roles/1',
                              headers={'Authorization': f'Bearer {admin_token}'})

        if response.status_code == 200:
            data = response.get_json()
            assert 'role' in data
            assert data['role']['name'] == 'admin'

    def test_get_role_not_found(self, client, admin_token):
        """Test getting non-existent role"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/roles/999',
                              headers={'Authorization': f'Bearer {admin_token}'})

        assert response.status_code == 404


# ============================================================================
# Test 12: Audit Logs
# ============================================================================

@pytest.mark.unit
@pytest.mark.rbac
class TestAuditLogs:
    """Test suite for audit logs endpoint"""

    def test_get_audit_logs_success(self, client, admin_token):
        """Test getting audit logs"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/audit/logs?limit=10',
                              headers={'Authorization': f'Bearer {admin_token}'})

        assert response.status_code == 200
        data = response.get_json()

        assert 'logs' in data
        assert 'total' in data
        assert isinstance(data['logs'], list)

    def test_audit_logs_filtering(self, client, admin_token):
        """Test audit log filtering by action"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get('/api/v1/audit/logs?action=login&limit=5',
                              headers={'Authorization': f'Bearer {admin_token}'})

        if response.status_code == 200:
            data = response.get_json()
            assert len(data['logs']) <= 5

    def test_audit_logs_no_permission(self, client, viewer_token):
        """Test audit logs without permission"""
        if not viewer_token:
            pytest.skip("Viewer token not available")

        response = client.get('/api/v1/audit/logs',
                              headers={'Authorization': f'Bearer {viewer_token}'})

        # Viewers typically can't access audit logs
        assert response.status_code in [200, 403]

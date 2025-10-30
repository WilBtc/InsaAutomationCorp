"""
Integration tests for auth.py API endpoints

Tests cover:
- Login success with valid credentials
- Login failure with invalid credentials
- Login failure with inactive user
- Login failure with missing user
- Token authentication on protected endpoints
- Protected endpoint access with valid token
- Protected endpoint access without token
- Protected endpoint access with invalid token
- Token refresh
- Password change
- Logout
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
import uuid

# Import auth router and dependencies
from core.api.routers.auth import router, LoginRequest, PasswordChangeRequest
from core.api.core.security import create_access_token, get_password_hash
from core.api.core.dependencies import get_current_user


@pytest.mark.integration
class TestLoginEndpoint:
    """Test /api/v1/auth/login endpoint"""

    @patch('core.api.routers.auth.get_db')
    @patch('core.api.routers.auth.verify_password')
    @patch('core.api.routers.auth.create_access_token')
    def test_login_success(self, mock_create_token, mock_verify, mock_get_db, sample_user, mock_db_connection):
        """
        Test successful login with valid credentials

        Arrange: Mock database with valid user, mock password verification
        Act: POST login request with valid credentials
        Assert: Returns 200, access token, and user info
        """
        # Arrange
        mock_cursor = MagicMock()
        user_tuple = (
            sample_user['id'],
            sample_user['email'],
            sample_user['full_name'],
            sample_user['password_hash'],
            sample_user['role'],
            sample_user['is_active']
        )
        mock_cursor.fetchone.return_value = user_tuple

        mock_db_connection.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db_connection
        mock_verify.return_value = True
        mock_create_token.return_value = "fake-jwt-token-12345"

        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        login_data = {
            "email": sample_user['email'],
            "password": sample_user['password']
        }

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert response_data["user"]["email"] == sample_user['email']
        assert response_data["user"]["role"] == sample_user['role']
        assert response_data["user"]["is_active"] is True

    @patch('core.api.routers.auth.get_db')
    @patch('core.api.routers.auth.verify_password')
    def test_login_invalid_credentials(self, mock_verify, mock_get_db, sample_user, mock_db_connection):
        """
        Test login failure with incorrect password

        Arrange: Mock database with user, password verification fails
        Act: POST login with wrong password
        Assert: Returns 401 Unauthorized
        """
        # Arrange
        mock_cursor = MagicMock()
        user_tuple = (
            sample_user['id'],
            sample_user['email'],
            sample_user['full_name'],
            sample_user['password_hash'],
            sample_user['role'],
            sample_user['is_active']
        )
        mock_cursor.fetchone.return_value = user_tuple

        mock_db_connection.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db_connection
        mock_verify.return_value = False  # Wrong password

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        login_data = {
            "email": sample_user['email'],
            "password": "WrongPassword123!"
        }

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @patch('core.api.routers.auth.get_db')
    @patch('core.api.routers.auth.verify_password')
    @patch('core.api.routers.auth.create_access_token')
    def test_login_inactive_user(self, mock_create_token, mock_verify, mock_get_db, sample_inactive_user, mock_db_connection):
        """
        Test login failure with inactive user account

        Arrange: Mock database with inactive user
        Act: POST login with valid credentials but inactive account
        Assert: Returns 403 Forbidden
        """
        # Arrange
        mock_cursor = MagicMock()
        user_tuple = (
            sample_inactive_user['id'],
            sample_inactive_user['email'],
            sample_inactive_user['full_name'],
            sample_inactive_user['password_hash'],
            sample_inactive_user['role'],
            sample_inactive_user['is_active']  # False
        )
        mock_cursor.fetchone.return_value = user_tuple

        mock_db_connection.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db_connection
        mock_verify.return_value = True

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        login_data = {
            "email": sample_inactive_user['email'],
            "password": sample_inactive_user['password']
        }

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 403
        assert "Account is inactive" in response.json()["detail"]

    @patch('core.api.routers.auth.get_db')
    def test_login_missing_user(self, mock_get_db, mock_db_connection):
        """
        Test login failure with non-existent user

        Arrange: Mock database returns no user
        Act: POST login with non-existent email
        Assert: Returns 401 Unauthorized
        """
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # User not found

        mock_db_connection.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db_connection

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        login_data = {
            "email": "nonexistent@example.com",
            "password": "AnyPassword123!"
        }

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @patch('core.api.routers.auth.get_db')
    def test_login_invalid_email_format(self, mock_get_db, mock_db_connection):
        """
        Test login with invalid email format

        Arrange: Invalid email format
        Act: POST login with malformed email
        Assert: Returns 422 Validation Error
        """
        # Arrange
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        login_data = {
            "email": "not-an-email",  # Invalid format
            "password": "Password123!"
        }

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestProtectedEndpoints:
    """Test protected endpoints requiring authentication"""

    @patch('core.api.core.dependencies.get_auth_db')
    def test_protected_endpoint_with_valid_token(self, mock_get_auth_db, sample_user, mock_settings):
        """
        Test accessing protected endpoint with valid token

        Arrange: Create valid JWT token, mock database with user
        Act: GET /me with valid Authorization header
        Assert: Returns 200 with user info
        """
        # Arrange
        with patch('core.api.core.security.settings', mock_settings):
            token = create_access_token(data={
                "sub": sample_user['id'],
                "email": sample_user['email'],
                "role": sample_user['role']
            })

        # Mock database response
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': sample_user['id'],
            'email': sample_user['email'],
            'full_name': sample_user['full_name'],
            'role': sample_user['role'],
            'is_active': True
        }
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_auth_db.return_value.__enter__.return_value = mock_db

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Act
        with patch('core.api.core.security.settings', mock_settings):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["email"] == sample_user['email']
        assert response_data["role"] == sample_user['role']

    def test_protected_endpoint_without_token(self):
        """
        Test accessing protected endpoint without token

        Arrange: No authentication token
        Act: GET /me without Authorization header
        Assert: Returns 403 Forbidden
        """
        # Arrange
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Act
        response = client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403

    @patch('core.api.core.dependencies.get_auth_db')
    def test_protected_endpoint_with_invalid_token(self, mock_get_auth_db, mock_settings):
        """
        Test accessing protected endpoint with invalid token

        Arrange: Invalid JWT token
        Act: GET /me with invalid token
        Assert: Returns 401 Unauthorized
        """
        # Arrange
        invalid_token = "invalid.jwt.token.string"

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Act
        with patch('core.api.core.security.settings', mock_settings):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {invalid_token}"}
            )

        # Assert
        assert response.status_code == 401

    @patch('core.api.core.dependencies.get_auth_db')
    def test_protected_endpoint_with_expired_token(self, mock_get_auth_db, sample_user, mock_settings):
        """
        Test accessing protected endpoint with expired token

        Arrange: Create expired JWT token
        Act: GET /me with expired token
        Assert: Returns 401 Unauthorized
        """
        # Arrange
        from jose import jwt
        expired_payload = {
            "sub": sample_user['id'],
            "email": sample_user['email'],
            "role": sample_user['role'],
            "exp": datetime.utcnow() - timedelta(minutes=30)  # Expired
        }

        expired_token = jwt.encode(
            expired_payload,
            mock_settings.SECRET_KEY,
            algorithm=mock_settings.ALGORITHM
        )

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Act
        with patch('core.api.core.security.settings', mock_settings):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {expired_token}"}
            )

        # Assert
        assert response.status_code == 401


@pytest.mark.integration
class TestTokenRefresh:
    """Test token refresh endpoint"""

    @patch('core.api.routers.auth.get_db')
    @patch('core.api.routers.auth.get_current_user')
    @patch('core.api.routers.auth.create_access_token')
    def test_token_refresh_success(self, mock_create_token, mock_get_user, mock_get_db, sample_user, mock_db_connection):
        """
        Test successful token refresh

        Arrange: Valid current user and token
        Act: POST /refresh with valid token
        Assert: Returns new access token
        """
        # Arrange
        mock_get_user.return_value = sample_user
        mock_create_token.return_value = "new-jwt-token-67890"
        mock_get_db.return_value = mock_db_connection

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Act
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer old-token-12345"}
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert response_data["access_token"] == "new-jwt-token-67890"


@pytest.mark.integration
class TestPasswordChange:
    """Test password change endpoint"""

    @patch('core.api.routers.auth.get_db')
    @patch('core.api.routers.auth.get_current_user')
    @patch('core.api.routers.auth.verify_password')
    @patch('core.api.routers.auth.get_password_hash')
    def test_password_change_success(self, mock_hash, mock_verify, mock_get_user, mock_get_db, sample_user, mock_db_connection):
        """
        Test successful password change

        Arrange: Valid user with correct old password
        Act: PUT /password with old and new password
        Assert: Returns success message
        """
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (sample_user['password_hash'],)

        mock_db_connection.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db_connection
        mock_get_user.return_value = sample_user
        mock_verify.return_value = True
        mock_hash.return_value = "new-hashed-password"

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        password_data = {
            "old_password": "OldPassword123!",
            "new_password": "NewSecurePassword456!"
        }

        # Act
        response = client.put(
            "/api/v1/auth/password",
            json=password_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]

    @patch('core.api.routers.auth.get_db')
    @patch('core.api.routers.auth.get_current_user')
    @patch('core.api.routers.auth.verify_password')
    def test_password_change_wrong_old_password(self, mock_verify, mock_get_user, mock_get_db, sample_user, mock_db_connection):
        """
        Test password change with incorrect old password

        Arrange: User with wrong old password
        Act: PUT /password with incorrect old password
        Assert: Returns 401 Unauthorized
        """
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (sample_user['password_hash'],)

        mock_db_connection.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db_connection
        mock_get_user.return_value = sample_user
        mock_verify.return_value = False  # Wrong old password

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        password_data = {
            "old_password": "WrongOldPassword123!",
            "new_password": "NewSecurePassword456!"
        }

        # Act
        response = client.put(
            "/api/v1/auth/password",
            json=password_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 401
        assert "Incorrect current password" in response.json()["detail"]

    @patch('core.api.routers.auth.get_current_user')
    def test_password_change_weak_new_password(self, mock_get_user, sample_user):
        """
        Test password change with weak new password (too short)

        Arrange: User with valid old password but weak new password
        Act: PUT /password with short new password
        Assert: Returns 400 Bad Request
        """
        # Arrange
        mock_get_user.return_value = sample_user

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        password_data = {
            "old_password": "OldPassword123!",
            "new_password": "short"  # Less than 8 characters
        }

        # Act
        response = client.put(
            "/api/v1/auth/password",
            json=password_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 400
        assert "at least 8 characters" in response.json()["detail"]


@pytest.mark.integration
class TestLogout:
    """Test logout endpoint"""

    @patch('core.api.routers.auth.get_db')
    @patch('core.api.routers.auth.get_current_user')
    def test_logout_success(self, mock_get_user, mock_get_db, sample_user, mock_db_connection):
        """
        Test successful logout

        Arrange: Authenticated user with valid token
        Act: POST /logout
        Assert: Returns success message, session deleted
        """
        # Arrange
        mock_get_user.return_value = sample_user
        mock_get_db.return_value = mock_db_connection

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Act
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer valid-token-12345"}
        )

        # Assert
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]

        # Verify session was deleted
        mock_db_connection.execute.assert_called()


@pytest.mark.integration
class TestAuthenticationEdgeCases:
    """Test edge cases and error scenarios"""

    def test_login_missing_email(self):
        """
        Test login with missing email field

        Arrange: Login data without email
        Act: POST /login
        Assert: Returns 422 Validation Error
        """
        # Arrange
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        login_data = {
            "password": "Password123!"
            # Missing email
        }

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422

    def test_login_missing_password(self):
        """
        Test login with missing password field

        Arrange: Login data without password
        Act: POST /login
        Assert: Returns 422 Validation Error
        """
        # Arrange
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        login_data = {
            "email": "test@example.com"
            # Missing password
        }

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 422

    @patch('core.api.routers.auth.get_db')
    def test_login_database_error(self, mock_get_db):
        """
        Test login when database error occurs

        Arrange: Database raises exception
        Act: POST /login
        Assert: Returns 500 or appropriate error
        """
        # Arrange
        mock_get_db.side_effect = Exception("Database connection failed")

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        login_data = {
            "email": "test@example.com",
            "password": "Password123!"
        }

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code >= 500  # Internal server error

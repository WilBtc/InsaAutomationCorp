"""
Comprehensive tests for JWT authentication system.

This module tests the authentication endpoints, token validation,
and role-based access control.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import jwt

from app import create_app
from app.core.auth import (
    hash_password,
    verify_password,
    generate_token,
    decode_token,
    TokenType,
    UserRole
)
from app.db import get_db_pool


@pytest.fixture
def app():
    """Create test Flask application."""
    os.environ["SKIP_DB_INIT"] = "true"
    os.environ["JWT_SECRET_KEY"] = "test_secret_key_at_least_32_characters_long_for_security"
    app = create_app({
        "TESTING": True,
        "DEBUG": False
    })
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_pool(monkeypatch):
    """Mock database pool."""
    mock_pool = Mock()
    monkeypatch.setattr("app.db.get_db_pool", lambda: mock_pool)
    return mock_pool


class TestPasswordHashing:
    """Tests for password hashing functionality."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "test_password_123"
        invalid_hash = "not_a_valid_hash"

        assert verify_password(password, invalid_hash) is False


class TestTokenGeneration:
    """Tests for JWT token generation and decoding."""

    def test_generate_access_token(self):
        """Test access token generation."""
        token = generate_token(
            user_id=1,
            username="testuser",
            role=UserRole.VIEWER.value,
            token_type=TokenType.ACCESS
        )

        assert token is not None
        assert len(token) > 0

        # Decode to verify
        payload = decode_token(token)
        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"
        assert payload["role"] == UserRole.VIEWER.value
        assert payload["type"] == TokenType.ACCESS.value

    def test_generate_refresh_token(self):
        """Test refresh token generation."""
        token = generate_token(
            user_id=1,
            username="testuser",
            role=UserRole.VIEWER.value,
            token_type=TokenType.REFRESH
        )

        assert token is not None
        payload = decode_token(token)
        assert payload["type"] == TokenType.REFRESH.value

    def test_decode_token_expired(self):
        """Test decoding expired token."""
        # Create expired token
        secret_key = os.getenv("JWT_SECRET_KEY")
        payload = {
            "user_id": 1,
            "username": "testuser",
            "role": "viewer",
            "type": "access",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2),
            "nbf": datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, secret_key, algorithm="HS256")

        with pytest.raises(Exception):  # Should raise AuthenticationError
            decode_token(expired_token)

    def test_decode_token_invalid(self):
        """Test decoding invalid token."""
        with pytest.raises(Exception):
            decode_token("invalid_token_string")


class TestLoginEndpoint:
    """Tests for /api/v1/auth/login endpoint."""

    def test_login_success(self, client, db_pool):
        """Test successful login."""
        # Mock database responses
        db_pool.execute_query.side_effect = [
            # First call: find user
            [(1, "testuser", hash_password("password123"), "viewer",
              datetime.utcnow(), None)],
            # Second call: update last_login
            None,
            # Third call: store refresh token
            None
        ]

        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["user"]["username"] == "testuser"

    def test_login_invalid_credentials(self, client, db_pool):
        """Test login with invalid credentials."""
        db_pool.execute_query.return_value = []  # No user found

        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "wrong"
        })

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "invalid_credentials"

    def test_login_wrong_password(self, client, db_pool):
        """Test login with wrong password."""
        db_pool.execute_query.return_value = [
            (1, "testuser", hash_password("correct_password"), "viewer",
             datetime.utcnow(), None)
        ]

        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrong_password"
        })

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "invalid_credentials"

    def test_login_missing_username(self, client):
        """Test login with missing username."""
        response = client.post("/api/v1/auth/login", json={
            "password": "password123"
        })

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_request"

    def test_login_missing_password(self, client):
        """Test login with missing password."""
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser"
        })

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_request"

    def test_login_no_body(self, client):
        """Test login with no request body."""
        response = client.post("/api/v1/auth/login")

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_request"


class TestRefreshEndpoint:
    """Tests for /api/v1/auth/refresh endpoint."""

    def test_refresh_success(self, client, db_pool):
        """Test successful token refresh."""
        refresh_token = generate_token(
            user_id=1,
            username="testuser",
            role=UserRole.VIEWER.value,
            token_type=TokenType.REFRESH
        )

        # Mock database response
        db_pool.execute_query.return_value = [
            (1, datetime.utcnow() + timedelta(days=7))
        ]

        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    def test_refresh_invalid_token_type(self, client, db_pool):
        """Test refresh with access token instead of refresh token."""
        access_token = generate_token(
            user_id=1,
            username="testuser",
            role=UserRole.VIEWER.value,
            token_type=TokenType.ACCESS
        )

        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": access_token
        })

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "invalid_token_type"

    def test_refresh_missing_token(self, client):
        """Test refresh with missing token."""
        response = client.post("/api/v1/auth/refresh", json={})

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_request"

    def test_refresh_expired_token(self, client, db_pool):
        """Test refresh with expired token in database."""
        refresh_token = generate_token(
            user_id=1,
            username="testuser",
            role=UserRole.VIEWER.value,
            token_type=TokenType.REFRESH
        )

        # Mock expired token in database
        db_pool.execute_query.side_effect = [
            # First call: find token
            [(1, datetime.utcnow() - timedelta(days=1))],  # Expired
            # Second call: delete expired token
            None
        ]

        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "token_expired"


class TestProtectedEndpoints:
    """Tests for protected endpoints with @require_auth decorator."""

    def test_access_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "authentication_required"

    def test_access_with_valid_token(self, client, db_pool):
        """Test accessing protected endpoint with valid token."""
        token = generate_token(
            user_id=1,
            username="testuser",
            role=UserRole.VIEWER.value,
            token_type=TokenType.ACCESS
        )

        # Mock database response
        db_pool.execute_query.return_value = [
            (1, "testuser", "viewer", datetime.utcnow(), datetime.utcnow())
        ]

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["username"] == "testuser"

    def test_access_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_admin_endpoint_as_viewer(self, client, db_pool):
        """Test accessing admin endpoint as viewer."""
        token = generate_token(
            user_id=1,
            username="viewer_user",
            role=UserRole.VIEWER.value,
            token_type=TokenType.ACCESS
        )

        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data["error"] == "insufficient_permissions"

    def test_admin_endpoint_as_admin(self, client, db_pool):
        """Test accessing admin endpoint as admin."""
        token = generate_token(
            user_id=1,
            username="admin_user",
            role=UserRole.ADMIN.value,
            token_type=TokenType.ACCESS
        )

        # Mock database response
        db_pool.execute_query.return_value = [
            (1, "admin_user", "admin", datetime.utcnow(), datetime.utcnow())
        ]

        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200


class TestUserManagement:
    """Tests for user management endpoints."""

    def test_create_user_as_admin(self, client, db_pool):
        """Test creating user as admin."""
        token = generate_token(
            user_id=1,
            username="admin",
            role=UserRole.ADMIN.value,
            token_type=TokenType.ACCESS
        )

        # Mock database responses
        db_pool.execute_query.side_effect = [
            # First call: check if user exists
            [],
            # Second call: create user
            [(2, "newuser", "viewer", datetime.utcnow())]
        ]

        response = client.post(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "password": "password123",
                "role": "viewer"
            }
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["user"]["username"] == "newuser"

    def test_create_user_duplicate(self, client, db_pool):
        """Test creating user with duplicate username."""
        token = generate_token(
            user_id=1,
            username="admin",
            role=UserRole.ADMIN.value,
            token_type=TokenType.ACCESS
        )

        # Mock user already exists
        db_pool.execute_query.return_value = [(1,)]

        response = client.post(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "existinguser",
                "password": "password123",
                "role": "viewer"
            }
        )

        assert response.status_code == 409
        data = response.get_json()
        assert data["error"] == "user_exists"

    def test_create_user_weak_password(self, client, db_pool):
        """Test creating user with weak password."""
        token = generate_token(
            user_id=1,
            username="admin",
            role=UserRole.ADMIN.value,
            token_type=TokenType.ACCESS
        )

        response = client.post(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "password": "short",  # Too short
                "role": "viewer"
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "weak_password"

    def test_create_user_invalid_role(self, client, db_pool):
        """Test creating user with invalid role."""
        token = generate_token(
            user_id=1,
            username="admin",
            role=UserRole.ADMIN.value,
            token_type=TokenType.ACCESS
        )

        response = client.post(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "password": "password123",
                "role": "invalid_role"
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_role"


class TestLogoutEndpoint:
    """Tests for /api/v1/auth/logout endpoint."""

    def test_logout_success(self, client, db_pool):
        """Test successful logout."""
        token = generate_token(
            user_id=1,
            username="testuser",
            role=UserRole.VIEWER.value,
            token_type=TokenType.ACCESS
        )

        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Logout successful"

    def test_logout_without_token(self, client):
        """Test logout without authentication."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

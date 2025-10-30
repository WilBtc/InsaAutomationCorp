"""
Unit tests for security.py - Password hashing and JWT token functions

Tests cover:
- Password hashing with bcrypt
- Password verification (correct and incorrect)
- JWT token creation
- JWT token decoding
- JWT token expiration
- Invalid token handling
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import bcrypt
from jose import jwt, JWTError

# Import functions to test
from core.api.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification functions"""

    def test_password_hashing(self):
        """
        Test that password hashing creates a valid bcrypt hash

        Arrange: Plain text password
        Act: Hash the password
        Assert: Hash is valid bcrypt format and not equal to plain password
        """
        # Arrange
        plain_password = "SecurePassword123!"

        # Act
        hashed = get_password_hash(plain_password)

        # Assert
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != plain_password
        assert hashed.startswith('$2b$')  # bcrypt prefix
        assert len(hashed) == 60  # bcrypt hash length

    def test_password_hashing_different_salts(self):
        """
        Test that same password produces different hashes (due to salt)

        Arrange: Same plain text password
        Act: Hash it twice
        Assert: Two different hashes are produced
        """
        # Arrange
        plain_password = "SecurePassword123!"

        # Act
        hash1 = get_password_hash(plain_password)
        hash2 = get_password_hash(plain_password)

        # Assert
        assert hash1 != hash2  # Different salts should produce different hashes

    def test_password_verification_correct(self):
        """
        Test password verification with correct password

        Arrange: Plain password and its hash
        Act: Verify the password
        Assert: Verification returns True
        """
        # Arrange
        plain_password = "CorrectPassword456!"
        hashed = get_password_hash(plain_password)

        # Act
        result = verify_password(plain_password, hashed)

        # Assert
        assert result is True

    def test_password_verification_incorrect(self):
        """
        Test password verification with incorrect password

        Arrange: Plain password, hash, and wrong password
        Act: Verify wrong password against hash
        Assert: Verification returns False
        """
        # Arrange
        correct_password = "CorrectPassword456!"
        wrong_password = "WrongPassword789!"
        hashed = get_password_hash(correct_password)

        # Act
        result = verify_password(wrong_password, hashed)

        # Assert
        assert result is False

    def test_password_verification_empty_password(self):
        """
        Test password verification with empty password

        Arrange: Empty password and a valid hash
        Act: Verify empty password
        Assert: Verification returns False
        """
        # Arrange
        valid_password = "ValidPassword123!"
        hashed = get_password_hash(valid_password)
        empty_password = ""

        # Act
        result = verify_password(empty_password, hashed)

        # Assert
        assert result is False

    def test_password_verification_case_sensitive(self):
        """
        Test that password verification is case-sensitive

        Arrange: Password with specific case and its hash
        Act: Verify with different case
        Assert: Verification returns False
        """
        # Arrange
        password_lower = "password123"
        password_upper = "PASSWORD123"
        hashed = get_password_hash(password_lower)

        # Act
        result = verify_password(password_upper, hashed)

        # Assert
        assert result is False


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and decoding"""

    @patch('core.api.core.security.settings')
    def test_jwt_token_creation(self, mock_settings):
        """
        Test JWT token creation with valid data

        Arrange: Mock settings and user data
        Act: Create access token
        Assert: Token is valid JWT string
        """
        # Arrange
        mock_settings.SECRET_KEY = "test-secret-key-do-not-use-in-production"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        user_data = {
            "sub": "123e4567-e89b-12d3-a456-426614174000",
            "email": "test@insaautomation.com",
            "role": "sales_rep"
        }

        # Act
        token = create_access_token(data=user_data)

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        decoded = jwt.decode(
            token,
            mock_settings.SECRET_KEY,
            algorithms=[mock_settings.ALGORITHM]
        )
        assert decoded["sub"] == user_data["sub"]
        assert decoded["email"] == user_data["email"]
        assert decoded["role"] == user_data["role"]
        assert "exp" in decoded

    @patch('core.api.core.security.settings')
    def test_jwt_token_creation_custom_expiry(self, mock_settings):
        """
        Test JWT token creation with custom expiration time

        Arrange: Mock settings and custom expiration delta
        Act: Create token with custom expiry
        Assert: Token expires at expected time
        """
        # Arrange
        mock_settings.SECRET_KEY = "test-secret-key-do-not-use-in-production"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        user_data = {"sub": "test-user-id"}
        custom_expiry = timedelta(minutes=60)

        # Act
        before_time = datetime.utcnow()
        token = create_access_token(data=user_data, expires_delta=custom_expiry)
        after_time = datetime.utcnow()

        # Assert
        decoded = jwt.decode(
            token,
            mock_settings.SECRET_KEY,
            algorithms=[mock_settings.ALGORITHM]
        )

        # Check expiration is approximately 60 minutes from now
        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_min = before_time + custom_expiry
        expected_max = after_time + custom_expiry

        assert expected_min <= exp_time <= expected_max

    @patch('core.api.core.security.settings')
    def test_jwt_token_decoding(self, mock_settings):
        """
        Test JWT token decoding with valid token

        Arrange: Create a valid token
        Act: Decode the token
        Assert: Decoded payload matches original data
        """
        # Arrange
        mock_settings.SECRET_KEY = "test-secret-key-do-not-use-in-production"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        user_data = {
            "sub": "user-123",
            "email": "user@example.com",
            "role": "admin"
        }
        token = create_access_token(data=user_data)

        # Act
        decoded = decode_access_token(token)

        # Assert
        assert decoded is not None
        assert decoded["sub"] == user_data["sub"]
        assert decoded["email"] == user_data["email"]
        assert decoded["role"] == user_data["role"]

    @patch('core.api.core.security.settings')
    def test_jwt_token_expiration(self, mock_settings):
        """
        Test that expired JWT tokens are rejected

        Arrange: Create token with past expiration
        Act: Try to decode expired token
        Assert: Returns None for expired token
        """
        # Arrange
        mock_settings.SECRET_KEY = "test-secret-key-do-not-use-in-production"
        mock_settings.ALGORITHM = "HS256"

        user_data = {"sub": "user-123"}
        expired_delta = timedelta(seconds=-10)  # Already expired

        # Create token that's already expired
        to_encode = user_data.copy()
        expire = datetime.utcnow() + expired_delta
        to_encode.update({"exp": expire})
        expired_token = jwt.encode(
            to_encode,
            mock_settings.SECRET_KEY,
            algorithm=mock_settings.ALGORITHM
        )

        # Act
        decoded = decode_access_token(expired_token)

        # Assert
        assert decoded is None

    @patch('core.api.core.security.settings')
    def test_jwt_invalid_token(self, mock_settings):
        """
        Test decoding invalid/malformed JWT token

        Arrange: Invalid token string
        Act: Try to decode invalid token
        Assert: Returns None for invalid token
        """
        # Arrange
        mock_settings.SECRET_KEY = "test-secret-key-do-not-use-in-production"
        mock_settings.ALGORITHM = "HS256"

        invalid_token = "not.a.valid.jwt.token.at.all"

        # Act
        decoded = decode_access_token(invalid_token)

        # Assert
        assert decoded is None

    @patch('core.api.core.security.settings')
    def test_jwt_token_wrong_secret(self, mock_settings):
        """
        Test decoding token with wrong secret key

        Arrange: Token signed with one key, decode with another
        Act: Try to decode with wrong key
        Assert: Returns None
        """
        # Arrange
        correct_secret = "correct-secret-key"
        wrong_secret = "wrong-secret-key"
        mock_settings.ALGORITHM = "HS256"

        user_data = {"sub": "user-123"}

        # Create token with correct secret
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, correct_secret, algorithm="HS256")

        # Try to decode with wrong secret
        mock_settings.SECRET_KEY = wrong_secret

        # Act
        decoded = decode_access_token(token)

        # Assert
        assert decoded is None

    @patch('core.api.core.security.settings')
    def test_jwt_token_missing_required_fields(self, mock_settings):
        """
        Test creating token without required fields

        Arrange: Empty data dict
        Act: Create token
        Assert: Token is created but contains exp field
        """
        # Arrange
        mock_settings.SECRET_KEY = "test-secret-key-do-not-use-in-production"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        empty_data = {}

        # Act
        token = create_access_token(data=empty_data)
        decoded = decode_access_token(token)

        # Assert
        assert decoded is not None
        assert "exp" in decoded  # Expiration should always be added

    @patch('core.api.core.security.settings')
    def test_jwt_token_with_special_characters(self, mock_settings):
        """
        Test JWT token with special characters in payload

        Arrange: User data with special characters
        Act: Create and decode token
        Assert: Special characters are preserved
        """
        # Arrange
        mock_settings.SECRET_KEY = "test-secret-key-do-not-use-in-production"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        user_data = {
            "sub": "user-123",
            "email": "test+tag@example.com",
            "name": "José María O'Brien"
        }

        # Act
        token = create_access_token(data=user_data)
        decoded = decode_access_token(token)

        # Assert
        assert decoded is not None
        assert decoded["email"] == user_data["email"]
        assert decoded["name"] == user_data["name"]


@pytest.mark.unit
class TestSecurityEdgeCases:
    """Test edge cases and error handling"""

    def test_verify_password_with_none_hash(self):
        """
        Test password verification when hash is None

        Arrange: Valid password and None hash
        Act: Verify password
        Assert: Raises exception or returns False
        """
        # Arrange
        password = "TestPassword123!"

        # Act & Assert
        with pytest.raises((AttributeError, ValueError, TypeError)):
            verify_password(password, None)

    def test_get_password_hash_empty_string(self):
        """
        Test hashing an empty password

        Arrange: Empty string password
        Act: Hash the password
        Assert: Hash is created (bcrypt allows empty passwords)
        """
        # Arrange
        empty_password = ""

        # Act
        hashed = get_password_hash(empty_password)

        # Assert
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed.startswith('$2b$')

    @patch('core.api.core.security.settings')
    def test_decode_empty_token(self, mock_settings):
        """
        Test decoding empty token string

        Arrange: Empty token string
        Act: Try to decode
        Assert: Returns None
        """
        # Arrange
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"

        # Act
        decoded = decode_access_token("")

        # Assert
        assert decoded is None

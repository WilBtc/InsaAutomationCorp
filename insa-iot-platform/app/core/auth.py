"""
JWT Authentication module for the Alkhorayef ESP IoT Platform.

This module provides JWT token generation, validation, and RBAC functionality.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import wraps
from enum import Enum

import jwt
import bcrypt
from flask import request, jsonify, g, Response

from .config import get_config
from .logging import get_logger
from .exceptions import AuthenticationError, AuthorizationError


logger = get_logger(__name__)


class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class TokenType(str, Enum):
    """Token types."""

    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password
        password_hash: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def generate_token(
    user_id: int,
    username: str,
    role: str,
    token_type: TokenType = TokenType.ACCESS
) -> str:
    """
    Generate a JWT token.

    Args:
        user_id: User ID
        username: Username
        role: User role
        token_type: Type of token (access or refresh)

    Returns:
        JWT token string

    Raises:
        AuthenticationError: If token generation fails
    """
    config = get_config()

    try:
        # Determine expiration time
        if token_type == TokenType.ACCESS:
            expire_minutes = int(os.getenv(
                "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
                "1440"  # 24 hours
            ))
            expire_delta = timedelta(minutes=expire_minutes)
        else:  # REFRESH
            expire_days = int(os.getenv(
                "JWT_REFRESH_TOKEN_EXPIRE_DAYS",
                "7"
            ))
            expire_delta = timedelta(days=expire_days)

        # Create token payload
        now = datetime.utcnow()
        expire = now + expire_delta

        payload: Dict[str, Any] = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "type": token_type.value,
            "iat": now,
            "exp": expire,
            "nbf": now,  # Not before
        }

        # Get secret key
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            raise AuthenticationError(
                message="JWT_SECRET_KEY not configured",
                details={"hint": "Set JWT_SECRET_KEY in environment"}
            )

        # Get algorithm
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        # Generate token
        token = jwt.encode(
            payload,
            secret_key,
            algorithm=algorithm
        )

        logger.info(
            f"Generated {token_type.value} token for user {username}",
            extra={
                "extra_fields": {
                    "user_id": user_id,
                    "username": username,
                    "role": role,
                    "token_type": token_type.value,
                    "expires_at": expire.isoformat()
                }
            }
        )

        return token

    except jwt.PyJWTError as e:
        logger.error(f"JWT generation error: {e}")
        raise AuthenticationError(
            message="Failed to generate token",
            details={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error generating token: {e}")
        raise AuthenticationError(
            message="Failed to generate token",
            details={"error": str(e)}
        )


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        # Get secret key
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            raise AuthenticationError(
                message="JWT_SECRET_KEY not configured",
                details={"hint": "Set JWT_SECRET_KEY in environment"}
            )

        # Get algorithm
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        # Decode token
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm]
        )

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired token presented")
        raise AuthenticationError(
            message="Token has expired",
            details={"error": "expired_token"}
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise AuthenticationError(
            message="Invalid token",
            details={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        raise AuthenticationError(
            message="Failed to decode token",
            details={"error": str(e)}
        )


def get_token_from_request() -> Optional[str]:
    """
    Extract JWT token from request headers.

    Returns:
        Token string or None
    """
    # Check Authorization header
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix

    # Check X-API-Key header (alternative)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key

    return None


def get_current_user() -> Dict[str, Any]:
    """
    Get current authenticated user from request context.

    Returns:
        User information dictionary

    Raises:
        AuthenticationError: If user is not authenticated
    """
    if not hasattr(g, 'current_user'):
        raise AuthenticationError(
            message="Not authenticated",
            details={"error": "no_user_context"}
        )

    return g.current_user


def require_auth(role: Optional[str] = None):
    """
    Decorator to require authentication and optionally check role.

    Args:
        role: Required role (admin, operator, viewer). If None, any authenticated user is allowed.

    Returns:
        Decorated function

    Example:
        @require_auth()
        def protected_endpoint():
            pass

        @require_auth(role="admin")
        def admin_only_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Extract token
                token = get_token_from_request()
                if not token:
                    logger.warning(
                        "Authentication required but no token provided",
                        extra={"extra_fields": {"endpoint": request.endpoint}}
                    )
                    return jsonify({
                        "error": "authentication_required",
                        "message": "Authentication required. Please provide a valid JWT token.",
                        "details": {
                            "hint": "Include 'Authorization: Bearer <token>' header"
                        }
                    }), 401

                # Decode and validate token
                payload = decode_token(token)

                # Verify token type is 'access'
                if payload.get("type") != TokenType.ACCESS.value:
                    logger.warning(
                        "Invalid token type for authentication",
                        extra={
                            "extra_fields": {
                                "token_type": payload.get("type"),
                                "expected": TokenType.ACCESS.value
                            }
                        }
                    )
                    return jsonify({
                        "error": "invalid_token_type",
                        "message": "Invalid token type. Access token required.",
                    }), 401

                # Store user in request context
                g.current_user = {
                    "user_id": payload.get("user_id"),
                    "username": payload.get("username"),
                    "role": payload.get("role"),
                }

                # Check role if specified
                if role:
                    user_role = payload.get("role")

                    # Admin has access to everything
                    if user_role == UserRole.ADMIN.value:
                        pass
                    # Check exact role match
                    elif user_role != role:
                        logger.warning(
                            f"Authorization failed: user role '{user_role}' != required role '{role}'",
                            extra={
                                "extra_fields": {
                                    "username": payload.get("username"),
                                    "user_role": user_role,
                                    "required_role": role,
                                    "endpoint": request.endpoint
                                }
                            }
                        )
                        return jsonify({
                            "error": "insufficient_permissions",
                            "message": f"This endpoint requires '{role}' role.",
                            "details": {
                                "your_role": user_role,
                                "required_role": role
                            }
                        }), 403

                logger.debug(
                    f"Authentication successful for user {payload.get('username')}",
                    extra={
                        "extra_fields": {
                            "user_id": payload.get("user_id"),
                            "username": payload.get("username"),
                            "role": payload.get("role"),
                            "endpoint": request.endpoint
                        }
                    }
                )

                # Call the actual endpoint function
                return f(*args, **kwargs)

            except AuthenticationError as e:
                return jsonify({
                    "error": "authentication_failed",
                    "message": e.message,
                    "details": e.details
                }), 401
            except AuthorizationError as e:
                return jsonify({
                    "error": "authorization_failed",
                    "message": e.message,
                    "details": e.details
                }), 403
            except Exception as e:
                logger.error(
                    f"Unexpected error in authentication: {e}",
                    exc_info=e
                )
                return jsonify({
                    "error": "internal_error",
                    "message": "An unexpected error occurred during authentication."
                }), 500

        return decorated_function
    return decorator


def create_default_admin_user(db_pool) -> Tuple[bool, str]:
    """
    Create default admin user if no users exist.

    Args:
        db_pool: Database connection pool

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Check if any users exist
        result = db_pool.execute_query(
            "SELECT COUNT(*) FROM users",
            fetch=True
        )

        user_count = result[0][0] if result else 0

        if user_count > 0:
            return True, "Users already exist, skipping default admin creation"

        # Create default admin user
        default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

        password_hash = hash_password(default_password)

        db_pool.execute_query(
            """
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (default_username, password_hash, UserRole.ADMIN.value, datetime.utcnow()),
            fetch=False
        )

        logger.warning(
            f"Created default admin user: {default_username}",
            extra={
                "extra_fields": {
                    "username": default_username,
                    "security_warning": "Change default password immediately!"
                }
            }
        )

        return True, f"Default admin user '{default_username}' created successfully"

    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}", exc_info=e)
        return False, f"Failed to create default admin user: {str(e)}"

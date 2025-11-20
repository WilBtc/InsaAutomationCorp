"""
Authentication endpoints for the Alkhorayef ESP IoT Platform.

This module provides login, token refresh, and logout endpoints.
"""

from datetime import datetime
from typing import Dict, Any

from flask import Blueprint, request, jsonify, Response

from app.core import get_logger
from app.core.auth import (
    generate_token,
    decode_token,
    verify_password,
    hash_password,
    get_current_user,
    require_auth,
    UserRole,
    TokenType
)
from app.core.exceptions import AuthenticationError, ValidationError
from app.db import get_db_pool


logger = get_logger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


# In-memory blacklist for revoked tokens (use Redis in production)
_revoked_tokens = set()


def is_token_revoked(token: str) -> bool:
    """Check if a token has been revoked."""
    return token in _revoked_tokens


def revoke_token(token: str) -> None:
    """Add a token to the revoked list."""
    _revoked_tokens.add(token)


@auth_bp.route("/login", methods=["POST"])
def login() -> Response:
    """
    Authenticate user and return JWT tokens.

    Request Body:
        {
            "username": "string",
            "password": "string"
        }

    Returns:
        JSON response with access and refresh tokens

    Status Codes:
        200: Login successful
        400: Invalid request body
        401: Invalid credentials
        500: Internal server error
    """
    try:
        # Parse request body
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "invalid_request",
                "message": "Request body is required"
            }), 400

        username = data.get("username")
        password = data.get("password")

        # Validate input
        if not username or not password:
            return jsonify({
                "error": "invalid_request",
                "message": "Username and password are required",
                "details": {
                    "missing_fields": [
                        field for field in ["username", "password"]
                        if not data.get(field)
                    ]
                }
            }), 400

        # Get database connection
        db_pool = get_db_pool()

        # Find user with tenant information
        result = db_pool.execute_query(
            """
            SELECT id, username, password_hash, role, created_at, last_login,
                   tenant_id, is_super_admin, is_active
            FROM users
            WHERE username = %s
            """,
            (username,),
            fetch=True
        )

        if not result:
            logger.warning(
                f"Login attempt for non-existent user: {username}",
                extra={"extra_fields": {"username": username}}
            )
            return jsonify({
                "error": "invalid_credentials",
                "message": "Invalid username or password"
            }), 401

        user = result[0]
        user_id, db_username, password_hash, role, created_at, last_login, tenant_id, is_super_admin, is_active = user

        # Check if user is active
        if not is_active:
            logger.warning(
                f"Login attempt for inactive user: {username}",
                extra={"extra_fields": {"username": username}}
            )
            return jsonify({
                "error": "account_inactive",
                "message": "Account is inactive"
            }), 401

        # Verify password
        if not verify_password(password, password_hash):
            logger.warning(
                f"Failed login attempt for user: {username}",
                extra={"extra_fields": {"username": username}}
            )
            return jsonify({
                "error": "invalid_credentials",
                "message": "Invalid username or password"
            }), 401

        # Generate tokens with tenant information
        access_token = generate_token(
            user_id=user_id,
            username=db_username,
            role=role,
            token_type=TokenType.ACCESS,
            tenant_id=tenant_id,
            is_super_admin=is_super_admin
        )

        refresh_token = generate_token(
            user_id=user_id,
            username=db_username,
            role=role,
            token_type=TokenType.REFRESH,
            tenant_id=tenant_id,
            is_super_admin=is_super_admin
        )

        # Update last login timestamp
        db_pool.execute_query(
            """
            UPDATE users
            SET last_login = %s
            WHERE id = %s
            """,
            (datetime.utcnow(), user_id),
            fetch=False
        )

        # Store refresh token in database
        db_pool.execute_query(
            """
            INSERT INTO refresh_tokens (token, user_id, created_at, expires_at)
            VALUES (%s, %s, %s, %s)
            """,
            (
                refresh_token,
                user_id,
                datetime.utcnow(),
                # Calculate expiration based on token
                decode_token(refresh_token)["exp"]
            ),
            fetch=False
        )

        logger.info(
            f"User logged in successfully: {username}",
            extra={
                "extra_fields": {
                    "user_id": user_id,
                    "username": username,
                    "role": role
                }
            }
        )

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": {
                "id": user_id,
                "username": db_username,
                "role": role,
                "created_at": created_at.isoformat() if created_at else None,
                "last_login": last_login.isoformat() if last_login else None
            }
        }), 200

    except AuthenticationError as e:
        logger.error(f"Authentication error during login: {e.message}")
        return jsonify({
            "error": "authentication_error",
            "message": e.message,
            "details": e.details
        }), 401
    except Exception as e:
        logger.error(
            "Unexpected error during login",
            exc_info=e
        )
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred during login"
        }), 500


@auth_bp.route("/refresh", methods=["POST"])
def refresh() -> Response:
    """
    Refresh access token using refresh token.

    Request Body:
        {
            "refresh_token": "string"
        }

    Returns:
        JSON response with new access token

    Status Codes:
        200: Refresh successful
        400: Invalid request body
        401: Invalid or expired refresh token
        500: Internal server error
    """
    try:
        # Parse request body
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "invalid_request",
                "message": "Request body is required"
            }), 400

        refresh_token = data.get("refresh_token")
        if not refresh_token:
            return jsonify({
                "error": "invalid_request",
                "message": "refresh_token is required"
            }), 400

        # Check if token is revoked
        if is_token_revoked(refresh_token):
            return jsonify({
                "error": "token_revoked",
                "message": "This refresh token has been revoked"
            }), 401

        # Decode and validate refresh token
        payload = decode_token(refresh_token)

        # Verify token type
        if payload.get("type") != TokenType.REFRESH.value:
            return jsonify({
                "error": "invalid_token_type",
                "message": "Invalid token type. Refresh token required."
            }), 401

        # Verify token exists in database and is not expired
        db_pool = get_db_pool()
        result = db_pool.execute_query(
            """
            SELECT user_id, expires_at
            FROM refresh_tokens
            WHERE token = %s
            """,
            (refresh_token,),
            fetch=True
        )

        if not result:
            return jsonify({
                "error": "invalid_token",
                "message": "Refresh token not found"
            }), 401

        user_id_db, expires_at = result[0]

        # Verify token hasn't expired in database
        if datetime.utcnow() > expires_at:
            # Clean up expired token
            db_pool.execute_query(
                "DELETE FROM refresh_tokens WHERE token = %s",
                (refresh_token,),
                fetch=False
            )
            return jsonify({
                "error": "token_expired",
                "message": "Refresh token has expired"
            }), 401

        # Generate new access token
        new_access_token = generate_token(
            user_id=payload["user_id"],
            username=payload["username"],
            role=payload["role"],
            token_type=TokenType.ACCESS
        )

        logger.info(
            f"Access token refreshed for user: {payload['username']}",
            extra={
                "extra_fields": {
                    "user_id": payload["user_id"],
                    "username": payload["username"]
                }
            }
        )

        return jsonify({
            "message": "Token refreshed successfully",
            "access_token": new_access_token,
            "token_type": "Bearer"
        }), 200

    except AuthenticationError as e:
        logger.error(f"Authentication error during token refresh: {e.message}")
        return jsonify({
            "error": "authentication_error",
            "message": e.message,
            "details": e.details
        }), 401
    except Exception as e:
        logger.error(
            "Unexpected error during token refresh",
            exc_info=e
        )
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred during token refresh"
        }), 500


@auth_bp.route("/logout", methods=["POST"])
@require_auth()
def logout() -> Response:
    """
    Logout user and invalidate tokens.

    Request Body (optional):
        {
            "refresh_token": "string"  # If provided, will be removed from database
        }

    Returns:
        JSON response confirming logout

    Status Codes:
        200: Logout successful
        401: Not authenticated
        500: Internal server error
    """
    try:
        current_user = get_current_user()

        # Get refresh token from request body if provided
        data = request.get_json() or {}
        refresh_token = data.get("refresh_token")

        db_pool = get_db_pool()

        # If refresh token provided, remove it from database
        if refresh_token:
            db_pool.execute_query(
                """
                DELETE FROM refresh_tokens
                WHERE token = %s AND user_id = %s
                """,
                (refresh_token, current_user["user_id"]),
                fetch=False
            )
            # Also add to in-memory revoked list
            revoke_token(refresh_token)

        # Optionally revoke all refresh tokens for this user
        if data.get("revoke_all_tokens", False):
            result = db_pool.execute_query(
                """
                SELECT token FROM refresh_tokens WHERE user_id = %s
                """,
                (current_user["user_id"],),
                fetch=True
            )
            if result:
                for (token,) in result:
                    revoke_token(token)

            db_pool.execute_query(
                "DELETE FROM refresh_tokens WHERE user_id = %s",
                (current_user["user_id"],),
                fetch=False
            )

        logger.info(
            f"User logged out: {current_user['username']}",
            extra={
                "extra_fields": {
                    "user_id": current_user["user_id"],
                    "username": current_user["username"]
                }
            }
        )

        return jsonify({
            "message": "Logout successful"
        }), 200

    except Exception as e:
        logger.error(
            "Unexpected error during logout",
            exc_info=e
        )
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred during logout"
        }), 500


@auth_bp.route("/me", methods=["GET"])
@require_auth()
def get_current_user_info() -> Response:
    """
    Get current authenticated user information.

    Returns:
        JSON response with user information

    Status Codes:
        200: Success
        401: Not authenticated
        500: Internal server error
    """
    try:
        current_user = get_current_user()

        # Get additional user details from database
        db_pool = get_db_pool()
        result = db_pool.execute_query(
            """
            SELECT id, username, role, created_at, last_login
            FROM users
            WHERE id = %s
            """,
            (current_user["user_id"],),
            fetch=True
        )

        if not result:
            return jsonify({
                "error": "user_not_found",
                "message": "User not found in database"
            }), 404

        user_id, username, role, created_at, last_login = result[0]

        return jsonify({
            "user": {
                "id": user_id,
                "username": username,
                "role": role,
                "created_at": created_at.isoformat() if created_at else None,
                "last_login": last_login.isoformat() if last_login else None
            }
        }), 200

    except Exception as e:
        logger.error(
            "Unexpected error getting user info",
            exc_info=e
        )
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred"
        }), 500


@auth_bp.route("/users", methods=["GET"])
@require_auth(role=UserRole.ADMIN.value)
def list_users() -> Response:
    """
    List all users (admin only).

    Returns:
        JSON response with list of users

    Status Codes:
        200: Success
        401: Not authenticated
        403: Not authorized (not admin)
        500: Internal server error
    """
    try:
        db_pool = get_db_pool()
        result = db_pool.execute_query(
            """
            SELECT id, username, role, created_at, last_login
            FROM users
            ORDER BY created_at DESC
            """,
            fetch=True
        )

        users = []
        for user_id, username, role, created_at, last_login in result:
            users.append({
                "id": user_id,
                "username": username,
                "role": role,
                "created_at": created_at.isoformat() if created_at else None,
                "last_login": last_login.isoformat() if last_login else None
            })

        return jsonify({
            "users": users,
            "count": len(users)
        }), 200

    except Exception as e:
        logger.error(
            "Unexpected error listing users",
            exc_info=e
        )
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred"
        }), 500


@auth_bp.route("/users", methods=["POST"])
@require_auth(role=UserRole.ADMIN.value)
def create_user() -> Response:
    """
    Create a new user (admin only).

    Request Body:
        {
            "username": "string",
            "password": "string",
            "role": "admin|operator|viewer"
        }

    Returns:
        JSON response with created user

    Status Codes:
        201: User created
        400: Invalid request
        401: Not authenticated
        403: Not authorized (not admin)
        409: User already exists
        500: Internal server error
    """
    try:
        # Parse request body
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "invalid_request",
                "message": "Request body is required"
            }), 400

        username = data.get("username")
        password = data.get("password")
        role = data.get("role", UserRole.VIEWER.value)

        # Validate input
        if not username or not password:
            return jsonify({
                "error": "invalid_request",
                "message": "Username and password are required"
            }), 400

        # Validate role
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            return jsonify({
                "error": "invalid_role",
                "message": f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            }), 400

        # Validate password strength
        if len(password) < 8:
            return jsonify({
                "error": "weak_password",
                "message": "Password must be at least 8 characters long"
            }), 400

        db_pool = get_db_pool()

        # Check if user already exists
        result = db_pool.execute_query(
            "SELECT id FROM users WHERE username = %s",
            (username,),
            fetch=True
        )

        if result:
            return jsonify({
                "error": "user_exists",
                "message": f"User '{username}' already exists"
            }), 409

        # Hash password
        password_hash = hash_password(password)

        # Create user
        result = db_pool.execute_query(
            """
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id, username, role, created_at
            """,
            (username, password_hash, role, datetime.utcnow()),
            fetch=True
        )

        user_id, db_username, db_role, created_at = result[0]

        logger.info(
            f"User created: {username}",
            extra={
                "extra_fields": {
                    "user_id": user_id,
                    "username": username,
                    "role": role,
                    "created_by": get_current_user()["username"]
                }
            }
        )

        return jsonify({
            "message": "User created successfully",
            "user": {
                "id": user_id,
                "username": db_username,
                "role": db_role,
                "created_at": created_at.isoformat() if created_at else None
            }
        }), 201

    except Exception as e:
        logger.error(
            "Unexpected error creating user",
            exc_info=e
        )
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred"
        }), 500

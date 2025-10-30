"""
FastAPI dependencies for authentication and authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth_db import get_auth_db
from .security import decode_access_token
import uuid

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get the current authenticated user from JWT token

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user_id from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query user from database
    with get_auth_db() as db:
        with db.cursor() as cursor:
            query = """
                SELECT id, email, full_name, role, is_active
                FROM users
                WHERE id = %s
            """
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if not user['is_active']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user"
                )

            # Update last_login
            update_query = """
                UPDATE users
                SET last_login = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            cursor.execute(update_query, (user_id,))
            db.commit()

            return {
                "id": str(user['id']),
                "email": user['email'],
                "full_name": user['full_name'],
                "role": user['role'],
                "is_active": user['is_active']
            }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current active user (convenience wrapper)
    """
    return current_user


async def require_role(required_role: str):
    """
    Dependency factory for role-based access control

    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: dict = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        role_hierarchy = {
            "viewer": 0,
            "sales_rep": 1,
            "sales_manager": 2,
            "admin": 3
        }

        user_level = role_hierarchy.get(current_user["role"], 0)
        required_level = role_hierarchy.get(required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )

        return current_user

    return role_checker

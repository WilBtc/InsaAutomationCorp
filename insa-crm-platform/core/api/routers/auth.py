"""
Authentication endpoints for login, logout, and token management
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import uuid

from ..core.database import get_db
from ..core.security import verify_password, get_password_hash, create_access_token
from ..core.dependencies import get_current_user, require_role
from ..core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
security = HTTPBearer()


# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token

    - **email**: User email address
    - **password**: User password
    """
    # Query user by email
    query = """
        SELECT id, email, full_name, password_hash, role, is_active
        FROM users
        WHERE email = %s
    """

    cursor = db.execute(query, (login_data.email,))
    user = cursor.fetchone()

    # Verify user exists
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id, email, full_name, password_hash, role, is_active = user

    # Verify user is active
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Verify password
    if not verify_password(login_data.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user_id), "email": email, "role": role}
    )

    # Create session record
    session_id = uuid.uuid4()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "Unknown")

    insert_session = """
        INSERT INTO user_sessions (id, user_id, token, expires_at, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    db.execute(insert_session, (session_id, user_id, access_token, expires_at, ip_address, user_agent))

    # Update last_login
    update_login = """
        UPDATE users
        SET last_login = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    db.execute(update_login, (user_id,))

    # Log activity
    log_activity = """
        INSERT INTO user_activity_log (id, user_id, action, resource_type, ip_address, created_at)
        VALUES (%s, %s, 'login', 'auth', %s, CURRENT_TIMESTAMP)
    """
    db.execute(log_activity, (uuid.uuid4(), user_id, ip_address))

    db.commit()

    return LoginResponse(
        access_token=access_token,
        user={
            "id": str(user_id),
            "email": email,
            "full_name": full_name,
            "role": role,
            "is_active": is_active
        }
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate session

    Requires authentication token in header:
    Authorization: Bearer <token>
    """
    # Get token from header
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    if token:
        # Delete session
        delete_session = """
            DELETE FROM user_sessions
            WHERE token = %s AND user_id = %s
        """
        db.execute(delete_session, (token, current_user["id"]))

        # Log activity
        log_activity = """
            INSERT INTO user_activity_log (id, user_id, action, resource_type, ip_address, created_at)
            VALUES (%s, %s, 'logout', 'auth', %s, CURRENT_TIMESTAMP)
        """
        ip_address = request.client.host if request.client else None
        db.execute(log_activity, (uuid.uuid4(), current_user["id"], ip_address))

        db.commit()

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current authenticated user information

    Requires authentication token in header:
    Authorization: Bearer <token>
    """
    return UserResponse(**current_user)


@router.post("/refresh")
async def refresh_token(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh JWT access token

    Requires authentication token in header:
    Authorization: Bearer <token>
    """
    # Create new access token
    new_token = create_access_token(
        data={
            "sub": current_user["id"],
            "email": current_user["email"],
            "role": current_user["role"]
        }
    )

    # Get old token
    auth_header = request.headers.get("authorization", "")
    old_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    if old_token:
        # Delete old session
        delete_old = """
            DELETE FROM user_sessions
            WHERE token = %s
        """
        db.execute(delete_old, (old_token,))

    # Create new session
    session_id = uuid.uuid4()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "Unknown")

    insert_session = """
        INSERT INTO user_sessions (id, user_id, token, expires_at, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    db.execute(insert_session, (session_id, current_user["id"], new_token, expires_at, ip_address, user_agent))

    db.commit()

    return {
        "access_token": new_token,
        "token_type": "bearer"
    }


@router.put("/password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password

    - **old_password**: Current password
    - **new_password**: New password (min 8 characters)
    """
    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )

    # Get current password hash
    query = """
        SELECT password_hash FROM users WHERE id = %s
    """
    cursor = db.execute(query, (current_user["id"],))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    current_hash = result[0]

    # Verify old password
    if not verify_password(password_data.old_password, current_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )

    # Hash new password
    new_hash = get_password_hash(password_data.new_password)

    # Update password
    update_query = """
        UPDATE users
        SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    db.execute(update_query, (new_hash, current_user["id"]))

    # Invalidate all sessions (force re-login)
    delete_sessions = """
        DELETE FROM user_sessions WHERE user_id = %s
    """
    db.execute(delete_sessions, (current_user["id"],))

    # Log activity
    log_activity = """
        INSERT INTO user_activity_log (id, user_id, action, resource_type, created_at)
        VALUES (%s, %s, 'password_change', 'auth', CURRENT_TIMESTAMP)
    """
    db.execute(log_activity, (uuid.uuid4(), current_user["id"]))

    db.commit()

    return {"message": "Password changed successfully. Please login again."}

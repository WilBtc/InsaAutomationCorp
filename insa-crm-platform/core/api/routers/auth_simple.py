"""Simple authentication endpoints using sync database"""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr
import uuid
import secrets

from ..core.auth_db import get_auth_db
from ..core.security import verify_password, create_access_token, get_password_hash
from ..core.dependencies import get_current_user
from ..core.config import settings
from ..core.rate_limit import limiter
from ..core.email import send_password_reset_email, send_invitation_email

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per IP per minute
async def login(login_data: LoginRequest, request: Request):
    """Login and get JWT token (rate limited to prevent brute-force attacks)"""
    with get_auth_db() as db:
        with db.cursor() as cursor:
            # Get user
            cursor.execute(
                "SELECT id, email, full_name, password_hash, role, is_active FROM users WHERE email = %s",
                (login_data.email,)
            )
            user = cursor.fetchone()

            if not user or not verify_password(login_data.password, user['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )

            if not user['is_active']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is inactive"
                )

            # Create token
            access_token = create_access_token(
                data={"sub": str(user['id']), "email": user['email'], "role": user['role']}
            )

            # Create session (store JWT ID in token_jti for token revocation)
            session_id = str(uuid.uuid4())
            token_jti = str(uuid.uuid4())  # JWT ID claim for token revocation
            expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            ip_address = request.client.host if request.client else None

            cursor.execute(
                "INSERT INTO user_sessions (id, user_id, token_jti, token_type, expires_at, ip_address, user_agent) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (session_id, str(user['id']), token_jti, 'access', expires_at, ip_address, request.headers.get("user-agent", "Unknown"))
            )

            # Update last login
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user['id'],))

            # Log activity
            cursor.execute(
                "INSERT INTO user_audit_log (user_id, action, resource_type, ip_address) VALUES (%s, 'login', 'auth', %s)",
                (str(user['id']), ip_address)
            )

            db.commit()

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": str(user['id']),
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "role": user['role']
                }
            }


@router.post("/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """Logout and invalidate session (mark as revoked)"""
    with get_auth_db() as db:
        with db.cursor() as cursor:
            # Mark all active sessions for this user as revoked
            cursor.execute(
                "UPDATE user_sessions SET is_revoked = TRUE, revoked_at = CURRENT_TIMESTAMP WHERE user_id = %s AND is_revoked = FALSE",
                (current_user["id"],)
            )
            cursor.execute(
                "INSERT INTO user_audit_log (user_id, action, resource_type) VALUES (%s, 'logout', 'auth')",
                (current_user["id"],)
            )
            db.commit()

    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user


@router.put("/password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    """Change password"""
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    with get_auth_db() as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (current_user["id"],))
            result = cursor.fetchone()

            if not result or not verify_password(old_password, result['password_hash']):
                raise HTTPException(status_code=401, detail="Incorrect current password")

            new_hash = get_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (new_hash, current_user["id"])
            )
            cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (current_user["id"],))
            cursor.execute(
                "INSERT INTO user_audit_log (user_id, action, resource_type) VALUES (%s, 'password_change', 'auth')",
                (current_user["id"],)
            )
            db.commit()

    return {"message": "Password changed successfully. Please login again."}


# Password Reset Endpoints

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
@limiter.limit("3/hour")  # Prevent abuse - max 3 requests per IP per hour
async def forgot_password(request_data: ForgotPasswordRequest, request: Request):
    """
    Request password reset email
    Rate limited to prevent abuse
    """
    with get_auth_db() as db:
        with db.cursor() as cursor:
            # Check if user exists (don't reveal if email exists or not for security)
            cursor.execute(
                "SELECT id, email, full_name FROM users WHERE email = %s AND is_active = TRUE",
                (request_data.email,)
            )
            user = cursor.fetchone()

            if user:
                # Generate secure random token
                reset_token = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(hours=1)
                ip_address = request.client.host if request.client else None

                # Store token
                cursor.execute(
                    "INSERT INTO password_reset_tokens (user_id, token, expires_at, ip_address) VALUES (%s, %s, %s, %s)",
                    (str(user['id']), reset_token, expires_at, ip_address)
                )

                # Log activity
                cursor.execute(
                    "INSERT INTO user_audit_log (user_id, action, resource_type, ip_address, details) VALUES (%s, 'password_reset_requested', 'auth', %s, %s)",
                    (str(user['id']), ip_address, '{"method": "email"}')
                )

                db.commit()

                # Send reset email
                base_url = "https://iac1.tailc58ea3.ts.net"
                send_password_reset_email(
                    email=user['email'],
                    full_name=user['full_name'],
                    reset_token=reset_token,
                    base_url=base_url
                )

    # Always return success message (don't reveal if email exists)
    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.get("/validate-reset-token/{token}")
async def validate_reset_token(token: str):
    """
    Validate if a password reset token is valid
    Used by frontend to check token before showing reset form
    """
    with get_auth_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    prt.id,
                    prt.expires_at,
                    prt.used_at,
                    u.email,
                    u.full_name
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = %s
                """,
                (token,)
            )
            token_data = cursor.fetchone()

            if not token_data:
                raise HTTPException(
                    status_code=404,
                    detail="Invalid reset token"
                )

            if token_data['used_at']:
                raise HTTPException(
                    status_code=400,
                    detail="Reset token has already been used"
                )

            if datetime.utcnow() > token_data['expires_at'].replace(tzinfo=None):
                raise HTTPException(
                    status_code=400,
                    detail="Reset token has expired"
                )

            return {
                "valid": True,
                "email": token_data['email'],
                "full_name": token_data['full_name']
            }


@router.post("/reset-password")
@limiter.limit("5/hour")  # Prevent brute-force attempts
async def reset_password(reset_data: ResetPasswordRequest, request: Request):
    """
    Reset password using valid token
    """
    if len(reset_data.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )

    with get_auth_db() as db:
        with db.cursor() as cursor:
            # Validate token
            cursor.execute(
                """
                SELECT
                    prt.id,
                    prt.user_id,
                    prt.expires_at,
                    prt.used_at
                FROM password_reset_tokens prt
                WHERE prt.token = %s
                """,
                (reset_data.token,)
            )
            token_data = cursor.fetchone()

            if not token_data:
                raise HTTPException(
                    status_code=404,
                    detail="Invalid reset token"
                )

            if token_data['used_at']:
                raise HTTPException(
                    status_code=400,
                    detail="Reset token has already been used"
                )

            if datetime.utcnow() > token_data['expires_at'].replace(tzinfo=None):
                raise HTTPException(
                    status_code=400,
                    detail="Reset token has expired"
                )

            # Update password
            new_hash = get_password_hash(reset_data.new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (new_hash, str(token_data['user_id']))
            )

            # Mark token as used
            cursor.execute(
                "UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP WHERE id = %s",
                (token_data['id'],)
            )

            # Invalidate all existing sessions for security
            cursor.execute(
                "UPDATE user_sessions SET is_revoked = TRUE, revoked_at = CURRENT_TIMESTAMP WHERE user_id = %s AND is_revoked = FALSE",
                (str(token_data['user_id']),)
            )

            # Log activity
            ip_address = request.client.host if request.client else None
            cursor.execute(
                "INSERT INTO user_audit_log (user_id, action, resource_type, ip_address, details) VALUES (%s, 'password_reset_completed', 'auth', %s, %s)",
                (str(token_data['user_id']), ip_address, '{"method": "token"}')
            )

            db.commit()

    return {
        "message": "Password has been reset successfully. Please login with your new password."
    }


# Invitation Acceptance Endpoints

class AcceptInvitationRequest(BaseModel):
    token: str
    password: str
    full_name: str


@router.get("/invitation/{token}")
async def get_invitation_details(token: str):
    """
    Get invitation details for display
    Used by frontend to show invitation info before acceptance
    """
    with get_auth_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    i.id, i.email, i.role, i.expires_at, i.accepted_at, i.metadata,
                    u.full_name as invited_by_name
                FROM user_invitations i
                JOIN users u ON i.invited_by = u.id
                WHERE i.token = %s
                """,
                (token,)
            )
            invitation = cursor.fetchone()

            if not invitation:
                raise HTTPException(
                    status_code=404,
                    detail="Invalid invitation token"
                )

            if invitation['accepted_at']:
                raise HTTPException(
                    status_code=400,
                    detail="Invitation has already been accepted"
                )

            if datetime.utcnow() > invitation['expires_at'].replace(tzinfo=None):
                raise HTTPException(
                    status_code=400,
                    detail="Invitation has expired"
                )

            return {
                "valid": True,
                "email": invitation['email'],
                "role": invitation['role'],
                "invited_by": invitation['invited_by_name'],
                "expires_at": invitation['expires_at'].isoformat()
            }


@router.post("/accept-invitation")
async def accept_invitation(invitation_data: AcceptInvitationRequest, request: Request):
    """
    Accept invitation and create user account
    Returns JWT token for auto-login
    """
    if len(invitation_data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )

    with get_auth_db() as db:
        with db.cursor() as cursor:
            # Validate invitation
            cursor.execute(
                """
                SELECT
                    i.id, i.email, i.role, i.expires_at, i.accepted_at, i.metadata
                FROM user_invitations i
                WHERE i.token = %s
                """,
                (invitation_data.token,)
            )
            invitation = cursor.fetchone()

            if not invitation:
                raise HTTPException(
                    status_code=404,
                    detail="Invalid invitation token"
                )

            if invitation['accepted_at']:
                raise HTTPException(
                    status_code=400,
                    detail="Invitation has already been accepted"
                )

            if datetime.utcnow() > invitation['expires_at'].replace(tzinfo=None):
                raise HTTPException(
                    status_code=400,
                    detail="Invitation has expired"
                )

            # Check if user already exists (edge case)
            cursor.execute("SELECT id FROM users WHERE email = %s", (invitation['email'],))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )

            # Create user account
            user_id = str(uuid.uuid4())
            password_hash = get_password_hash(invitation_data.password)

            # Get metadata
            import json
            metadata = json.loads(invitation['metadata']) if invitation['metadata'] else {}

            cursor.execute(
                """
                INSERT INTO users (id, email, full_name, password_hash, role, department, territory, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                """,
                (
                    user_id,
                    invitation['email'],
                    invitation_data.full_name,
                    password_hash,
                    invitation['role'],
                    metadata.get('department'),
                    metadata.get('territory')
                )
            )

            # Mark invitation as accepted
            cursor.execute(
                "UPDATE user_invitations SET accepted_at = CURRENT_TIMESTAMP WHERE id = %s",
                (invitation['id'],)
            )

            # Log activity
            ip_address = request.client.host if request.client else None
            cursor.execute(
                "INSERT INTO user_audit_log (user_id, action, resource_type, ip_address, details) VALUES (%s, 'invitation_accepted', 'auth', %s, %s)",
                (user_id, ip_address, f'{{"invitation_id": {invitation["id"]}}}')
            )

            db.commit()

            # Create JWT token for auto-login
            access_token = create_access_token(
                data={"sub": user_id, "email": invitation['email'], "role": invitation['role']}
            )

            # Create session
            session_id = str(uuid.uuid4())
            token_jti = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

            cursor.execute(
                "INSERT INTO user_sessions (id, user_id, token_jti, token_type, expires_at, ip_address, user_agent) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (session_id, user_id, token_jti, 'access', expires_at, ip_address, request.headers.get("user-agent", "Unknown"))
            )
            db.commit()

            return {
                "message": "Account created successfully",
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user_id,
                    "email": invitation['email'],
                    "full_name": invitation_data.full_name,
                    "role": invitation['role']
                }
            }

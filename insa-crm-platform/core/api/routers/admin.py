"""
Admin endpoints for user management
Requires admin role for all operations
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid
import secrets

from ..core.auth_db import get_auth_db
from ..core.security import get_password_hash
from ..core.dependencies import get_current_user
from ..core.rate_limit import limiter
from ..core.email import send_invitation_email

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# Dependency to require admin role
def require_admin(current_user: dict = Depends(get_current_user)):
    """Ensure user has admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Models

class InviteUserRequest(BaseModel):
    email: EmailStr
    role: str = "user"
    department: Optional[str] = None
    territory: Optional[str] = None


class AcceptInvitationRequest(BaseModel):
    token: str
    password: str
    full_name: str


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    territory: Optional[str] = None


# User Management Endpoints

@router.get("/users")
async def list_users(
    limit: int = 50,
    offset: int = 0,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(require_admin)
):
    """
    List all users with pagination and filters
    Admin only
    """
    with get_auth_db() as db:
        with db.cursor() as cursor:
            # Build query
            query = "SELECT id, email, full_name, role, department, territory, is_active, created_at, last_login FROM users WHERE 1=1"
            params = []

            if role:
                query += " AND role = %s"
                params.append(role)

            if is_active is not None:
                query += " AND is_active = %s"
                params.append(is_active)

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            users = cursor.fetchall()

            # Get total count
            count_query = "SELECT COUNT(*) as total FROM users WHERE 1=1"
            count_params = []
            if role:
                count_query += " AND role = %s"
                count_params.append(role)
            if is_active is not None:
                count_query += " AND is_active = %s"
                count_params.append(is_active)

            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']

            return {
                "users": [dict(u) for u in users],
                "total": total,
                "limit": limit,
                "offset": offset
            }


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """Get detailed user information"""
    with get_auth_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id, email, full_name, role, department, territory,
                    phone, is_active, created_at, updated_at, last_login
                FROM users
                WHERE id = %s
                """,
                (user_id,)
            )
            user = cursor.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            return dict(user)


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    updates: UpdateUserRequest,
    current_user: dict = Depends(require_admin)
):
    """Update user information (admin only)"""
    # Prevent admin from deactivating themselves
    if user_id == current_user["id"] and updates.is_active is False:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account"
        )

    with get_auth_db() as db:
        with db.cursor() as cursor:
            # Build update query
            update_fields = []
            params = []

            if updates.role is not None:
                update_fields.append("role = %s")
                params.append(updates.role)

            if updates.is_active is not None:
                update_fields.append("is_active = %s")
                params.append(updates.is_active)

            if updates.department is not None:
                update_fields.append("department = %s")
                params.append(updates.department)

            if updates.territory is not None:
                update_fields.append("territory = %s")
                params.append(updates.territory)

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)

            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, params)

            # Log activity
            cursor.execute(
                "INSERT INTO user_audit_log (user_id, action, resource_type, details) VALUES (%s, 'user_updated', 'admin', %s)",
                (current_user["id"], f'{{"target_user_id": "{user_id}", "updates": {updates.model_dump_json()}}}')
            )

            db.commit()

            return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete user (admin only, cannot delete yourself)"""
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )

    with get_auth_db() as db:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")

            # Log activity
            cursor.execute(
                "INSERT INTO user_audit_log (user_id, action, resource_type, details) VALUES (%s, 'user_deleted', 'admin', %s)",
                (current_user["id"], f'{{"deleted_user_id": "{user_id}"}}')
            )

            db.commit()

            return {"message": "User deleted successfully"}


# Invitation Management Endpoints

@router.post("/invitations")
@limiter.limit("10/hour")  # Prevent invitation spam
async def create_invitation(
    invite_data: InviteUserRequest,
    request: Request,
    current_user: dict = Depends(require_admin)
):
    """
    Create user invitation (admin only)
    Sends email with invitation link
    Rate limited to 10 per hour
    """
    with get_auth_db() as db:
        with db.cursor() as cursor:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (invite_data.email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )

            # Check if active invitation exists
            cursor.execute(
                "SELECT id FROM user_invitations WHERE email = %s AND accepted_at IS NULL AND expires_at > CURRENT_TIMESTAMP",
                (invite_data.email,)
            )
            existing_invitation = cursor.fetchone()

            if existing_invitation:
                raise HTTPException(
                    status_code=400,
                    detail="Active invitation already exists for this email"
                )

            # Generate secure token
            invitation_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=7)

            # Store invitation
            metadata = {}
            if invite_data.department:
                metadata['department'] = invite_data.department
            if invite_data.territory:
                metadata['territory'] = invite_data.territory

            cursor.execute(
                "INSERT INTO user_invitations (email, token, role, invited_by, expires_at, metadata) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (invite_data.email, invitation_token, invite_data.role, current_user["id"], expires_at, str(metadata))
            )
            invitation_id = cursor.fetchone()['id']

            # Log activity
            cursor.execute(
                "INSERT INTO user_audit_log (user_id, action, resource_type, details) VALUES (%s, 'invitation_created', 'admin', %s)",
                (current_user["id"], f'{{"invitation_id": {invitation_id}, "email": "{invite_data.email}", "role": "{invite_data.role}"}}')
            )

            db.commit()

            # Send invitation email
            base_url = "https://iac1.tailc58ea3.ts.net"
            send_invitation_email(
                email=invite_data.email,
                role=invite_data.role,
                invited_by_name=current_user.get("full_name", "Admin"),
                invitation_token=invitation_token,
                base_url=base_url
            )

            return {
                "message": "Invitation sent successfully",
                "invitation_id": invitation_id,
                "expires_at": expires_at.isoformat()
            }


@router.get("/invitations")
async def list_invitations(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,  # pending, accepted, expired
    current_user: dict = Depends(require_admin)
):
    """List all invitations with filters (admin only)"""
    with get_auth_db() as db:
        with db.cursor() as cursor:
            query = """
                SELECT
                    i.id, i.email, i.role, i.expires_at, i.accepted_at, i.created_at,
                    u.full_name as invited_by_name
                FROM user_invitations i
                JOIN users u ON i.invited_by = u.id
                WHERE 1=1
            """
            params = []

            if status == "pending":
                query += " AND i.accepted_at IS NULL AND i.expires_at > CURRENT_TIMESTAMP"
            elif status == "accepted":
                query += " AND i.accepted_at IS NOT NULL"
            elif status == "expired":
                query += " AND i.accepted_at IS NULL AND i.expires_at <= CURRENT_TIMESTAMP"

            query += " ORDER BY i.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            invitations = cursor.fetchall()

            return {
                "invitations": [dict(inv) for inv in invitations],
                "limit": limit,
                "offset": offset
            }


@router.delete("/invitations/{invitation_id}")
async def cancel_invitation(
    invitation_id: int,
    current_user: dict = Depends(require_admin)
):
    """Cancel pending invitation (admin only)"""
    with get_auth_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                "DELETE FROM user_invitations WHERE id = %s AND accepted_at IS NULL",
                (invitation_id,)
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Invitation not found or already accepted"
                )

            # Log activity
            cursor.execute(
                "INSERT INTO user_audit_log (user_id, action, resource_type, details) VALUES (%s, 'invitation_cancelled', 'admin', %s)",
                (current_user["id"], f'{{"invitation_id": {invitation_id}}}')
            )

            db.commit()

            return {"message": "Invitation cancelled successfully"}


# Activity Log

@router.get("/activity-log")
async def get_activity_log(
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Get user activity audit log (admin only)"""
    with get_auth_db() as db:
        with db.cursor() as cursor:
            query = """
                SELECT
                    al.id, al.action, al.resource_type, al.ip_address,
                    al.details, al.created_at,
                    u.email as user_email, u.full_name
                FROM user_audit_log al
                LEFT JOIN users u ON al.user_id = u.id
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND al.user_id = %s"
                params.append(user_id)

            if action:
                query += " AND al.action = %s"
                params.append(action)

            query += " ORDER BY al.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            logs = cursor.fetchall()

            return {
                "logs": [dict(log) for log in logs],
                "limit": limit,
                "offset": offset
            }

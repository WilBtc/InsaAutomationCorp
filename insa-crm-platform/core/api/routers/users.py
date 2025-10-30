"""
User management endpoints (admin only)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import uuid

from ..core.database import get_db
from ..core.security import get_password_hash
from ..core.dependencies import require_role

router = APIRouter(prefix="/api/v1/users", tags=["users"])


# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "sales_rep"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str]


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only)

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    # Count total users
    count_query = "SELECT COUNT(*) FROM users"
    cursor = db.execute(count_query)
    total = cursor.fetchone()[0]

    # Get users
    query = """
        SELECT id, email, full_name, role, is_active, created_at, last_login
        FROM users
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    cursor = db.execute(query, (limit, skip))
    users = cursor.fetchall()

    users_list = [
        UserResponse(
            id=str(user[0]),
            email=user[1],
            full_name=user[2],
            role=user[3],
            is_active=user[4],
            created_at=str(user[5]),
            last_login=str(user[6]) if user[6] else None
        )
        for user in users
    ]

    return UserListResponse(users=users_list, total=total)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only)

    - **email**: User email (must be unique)
    - **full_name**: User's full name
    - **password**: Initial password (min 8 characters)
    - **role**: User role (admin, sales_manager, sales_rep, viewer)
    """
    # Validate password
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Validate role
    valid_roles = ["admin", "sales_manager", "sales_rep", "viewer"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    # Check if email already exists
    check_query = "SELECT id FROM users WHERE email = %s"
    cursor = db.execute(check_query, (user_data.email,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    password_hash = get_password_hash(user_data.password)

    # Insert user
    user_id = uuid.uuid4()
    insert_query = """
        INSERT INTO users (id, email, full_name, password_hash, role, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s::user_role, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING id, email, full_name, role, is_active, created_at, last_login
    """

    cursor = db.execute(
        insert_query,
        (user_id, user_data.email, user_data.full_name, password_hash, user_data.role)
    )
    new_user = cursor.fetchone()

    # Log activity
    log_activity = """
        INSERT INTO user_activity_log (id, user_id, action, resource_type, resource_id, created_at)
        VALUES (%s, %s, 'create_user', 'user', %s, CURRENT_TIMESTAMP)
    """
    db.execute(log_activity, (uuid.uuid4(), current_user["id"], str(user_id)))

    db.commit()

    return UserResponse(
        id=str(new_user[0]),
        email=new_user[1],
        full_name=new_user[2],
        role=new_user[3],
        is_active=new_user[4],
        created_at=str(new_user[5]),
        last_login=str(new_user[6]) if new_user[6] else None
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only)
    """
    query = """
        SELECT id, email, full_name, role, is_active, created_at, last_login
        FROM users
        WHERE id = %s
    """

    cursor = db.execute(query, (user_id,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user[0]),
        email=user[1],
        full_name=user[2],
        role=user[3],
        is_active=user[4],
        created_at=str(user[5]),
        last_login=str(user[6]) if user[6] else None
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Update user (admin only)

    - **full_name**: New full name (optional)
    - **role**: New role (optional)
    - **is_active**: Active status (optional)
    """
    # Check if user exists
    check_query = "SELECT id FROM users WHERE id = %s"
    cursor = db.execute(check_query, (user_id,))
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Build update query dynamically
    updates = []
    params = []

    if user_data.full_name is not None:
        updates.append("full_name = %s")
        params.append(user_data.full_name)

    if user_data.role is not None:
        valid_roles = ["admin", "sales_manager", "sales_rep", "viewer"]
        if user_data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        updates.append("role = %s::user_role")
        params.append(user_data.role)

    if user_data.is_active is not None:
        updates.append("is_active = %s")
        params.append(user_data.is_active)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(user_id)

    update_query = f"""
        UPDATE users
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, email, full_name, role, is_active, created_at, last_login
    """

    cursor = db.execute(update_query, params)
    updated_user = cursor.fetchone()

    # Log activity
    log_activity = """
        INSERT INTO user_activity_log (id, user_id, action, resource_type, resource_id, created_at)
        VALUES (%s, %s, 'update_user', 'user', %s, CURRENT_TIMESTAMP)
    """
    db.execute(log_activity, (uuid.uuid4(), current_user["id"], user_id))

    db.commit()

    return UserResponse(
        id=str(updated_user[0]),
        email=updated_user[1],
        full_name=updated_user[2],
        role=updated_user[3],
        is_active=updated_user[4],
        created_at=str(updated_user[5]),
        last_login=str(updated_user[6]) if updated_user[6] else None
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Deactivate user (soft delete, admin only)

    Note: This deactivates the user but does not delete the record
    """
    # Prevent self-deletion
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Check if user exists
    check_query = "SELECT id FROM users WHERE id = %s"
    cursor = db.execute(check_query, (user_id,))
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Deactivate user
    update_query = """
        UPDATE users
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    db.execute(update_query, (user_id,))

    # Invalidate all sessions
    delete_sessions = """
        DELETE FROM user_sessions WHERE user_id = %s
    """
    db.execute(delete_sessions, (user_id,))

    # Log activity
    log_activity = """
        INSERT INTO user_activity_log (id, user_id, action, resource_type, resource_id, created_at)
        VALUES (%s, %s, 'delete_user', 'user', %s, CURRENT_TIMESTAMP)
    """
    db.execute(log_activity, (uuid.uuid4(), current_user["id"], user_id))

    db.commit()

    return {"message": "User deactivated successfully"}

#!/usr/bin/env python3
"""
Tenant Manager
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 6

Provides tenant management functionality including:
- Tenant CRUD operations
- User management within tenants
- Quota checking and enforcement
- Tenant statistics and analytics
- Invitation system

Author: INSA Automation Corp
Date: October 28, 2025
"""

import logging
import secrets
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TenantManagerException(Exception):
    """Custom exception for tenant management errors."""
    pass


class TenantManager:
    """
    Manages multi-tenant operations.

    Features:
    - Tenant creation, retrieval, update, deletion
    - User assignment to tenants with roles
    - Quota validation and enforcement
    - Invitation system
    - Tenant statistics and analytics
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize tenant manager.

        Args:
            db_config: Database configuration dictionary
        """
        self.db_config = db_config
        logger.info("TenantManager initialized")

    def __enter__(self):
        """Context manager entry."""
        self.conn = psycopg2.connect(**self.db_config)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()

    # =========================================================================
    # Tenant CRUD Operations
    # =========================================================================

    def create_tenant(
        self,
        name: str,
        slug: str,
        tier: str = 'starter',
        max_devices: Optional[int] = None,
        max_users: Optional[int] = None,
        max_retention_days: int = 90,
        enabled_features: Optional[Dict] = None,
        created_by: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new tenant.

        Args:
            name: Organization name
            slug: URL-friendly identifier (e.g., 'acme-corp')
            tier: Tenant tier (starter, professional, enterprise)
            max_devices: Device quota (None = unlimited)
            max_users: User quota (None = unlimited)
            max_retention_days: Data retention period
            enabled_features: Feature flags dict
            created_by: User ID who created tenant
            **kwargs: Additional metadata

        Returns:
            Created tenant dict

        Raises:
            TenantManagerException: If tenant creation fails
        """
        try:
            if enabled_features is None:
                enabled_features = {
                    'ml': True,
                    'advanced_analytics': True,
                    'mobile': True,
                    'retention': True
                }

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO tenants (
                        name, slug, tier, max_devices, max_users,
                        max_retention_days, enabled_features, created_by, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb
                    )
                    RETURNING *
                """, (
                    name, slug, tier, max_devices, max_users,
                    max_retention_days,
                    psycopg2.extras.Json(enabled_features),
                    created_by,
                    psycopg2.extras.Json(kwargs)
                ))

                tenant = dict(cursor.fetchone())
                logger.info(f"Tenant created: {name} ({tenant['id']})")
                return tenant

        except psycopg2.IntegrityError as e:
            if 'slug' in str(e):
                raise TenantManagerException(f"Tenant slug already exists: {slug}")
            raise TenantManagerException(f"Failed to create tenant: {e}")
        except Exception as e:
            raise TenantManagerException(f"Failed to create tenant: {e}")

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant by ID.

        Args:
            tenant_id: UUID of tenant

        Returns:
            Tenant dict or None if not found
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM tenants WHERE id = %s
                """, (tenant_id,))

                result = cursor.fetchone()
                return dict(result) if result else None

        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            return None

    def get_tenant_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant by slug.

        Args:
            slug: Tenant slug

        Returns:
            Tenant dict or None if not found
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM tenants WHERE slug = %s
                """, (slug,))

                result = cursor.fetchone()
                return dict(result) if result else None

        except Exception as e:
            logger.error(f"Failed to get tenant by slug {slug}: {e}")
            return None

    def list_tenants(
        self,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all tenants with optional filtering.

        Args:
            status: Filter by status (active, suspended, trial, churned)
            tier: Filter by tier (starter, professional, enterprise)
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of tenant dicts
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM tenants WHERE 1=1"
                params = []

                if status:
                    query += " AND status = %s"
                    params.append(status)

                if tier:
                    query += " AND tier = %s"
                    params.append(tier)

                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to list tenants: {e}")
            return []

    def update_tenant(
        self,
        tenant_id: str,
        **updates
    ) -> Optional[Dict[str, Any]]:
        """
        Update tenant fields.

        Args:
            tenant_id: UUID of tenant
            **updates: Fields to update (name, tier, max_devices, etc.)

        Returns:
            Updated tenant dict or None if not found

        Raises:
            TenantManagerException: If update fails
        """
        try:
            if not updates:
                raise TenantManagerException("No updates provided")

            # Build dynamic UPDATE query
            set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
            set_clause += ", updated_at = NOW()"

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(f"""
                    UPDATE tenants
                    SET {set_clause}
                    WHERE id = %s
                    RETURNING *
                """, list(updates.values()) + [tenant_id])

                result = cursor.fetchone()
                if result:
                    logger.info(f"Tenant updated: {tenant_id}")
                    return dict(result)
                else:
                    logger.warning(f"Tenant not found: {tenant_id}")
                    return None

        except Exception as e:
            raise TenantManagerException(f"Failed to update tenant: {e}")

    def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete tenant (CASCADE deletes all related data).

        Args:
            tenant_id: UUID of tenant

        Returns:
            True if deleted, False if not found

        Warning:
            This is a destructive operation that deletes ALL tenant data.
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM tenants WHERE id = %s
                """, (tenant_id,))

                deleted = cursor.rowcount > 0
                if deleted:
                    logger.warning(f"Tenant DELETED: {tenant_id}")
                return deleted

        except Exception as e:
            logger.error(f"Failed to delete tenant: {e}")
            return False

    # =========================================================================
    # Tenant User Management
    # =========================================================================

    def add_user_to_tenant(
        self,
        tenant_id: str,
        user_id: str,
        role_id: int,
        is_tenant_admin: bool = False
    ) -> Dict[str, Any]:
        """
        Add user to tenant with role.

        Args:
            tenant_id: UUID of tenant
            user_id: UUID of user
            role_id: Role ID (from roles table)
            is_tenant_admin: Whether user is tenant admin

        Returns:
            Tenant user mapping dict

        Raises:
            TenantManagerException: If operation fails
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO tenant_users (tenant_id, user_id, role_id, is_tenant_admin)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                """, (tenant_id, user_id, role_id, is_tenant_admin))

                result = dict(cursor.fetchone())
                logger.info(f"User {user_id} added to tenant {tenant_id}")
                return result

        except psycopg2.IntegrityError as e:
            if 'unique' in str(e).lower():
                raise TenantManagerException("User already in tenant")
            raise TenantManagerException(f"Failed to add user to tenant: {e}")
        except Exception as e:
            raise TenantManagerException(f"Failed to add user to tenant: {e}")

    def remove_user_from_tenant(
        self,
        tenant_id: str,
        user_id: str
    ) -> bool:
        """
        Remove user from tenant.

        Args:
            tenant_id: UUID of tenant
            user_id: UUID of user

        Returns:
            True if removed, False if not found
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM tenant_users
                    WHERE tenant_id = %s AND user_id = %s
                """, (tenant_id, user_id))

                removed = cursor.rowcount > 0
                if removed:
                    logger.info(f"User {user_id} removed from tenant {tenant_id}")
                return removed

        except Exception as e:
            logger.error(f"Failed to remove user from tenant: {e}")
            return False

    def list_tenant_users(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        List all users in a tenant.

        Args:
            tenant_id: UUID of tenant

        Returns:
            List of user dicts with role information
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        tu.id,
                        tu.tenant_id,
                        tu.user_id,
                        u.email,
                        u.full_name,
                        tu.role_id,
                        r.name as role_name,
                        r.description as role_description,
                        tu.is_tenant_admin,
                        tu.created_at
                    FROM tenant_users tu
                    JOIN users u ON tu.user_id = u.id
                    JOIN roles r ON tu.role_id = r.id
                    WHERE tu.tenant_id = %s
                    ORDER BY tu.created_at ASC
                """, (tenant_id,))

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to list tenant users: {e}")
            return []

    def update_user_role(
        self,
        tenant_id: str,
        user_id: str,
        role_id: int,
        is_tenant_admin: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update user's role in tenant.

        Args:
            tenant_id: UUID of tenant
            user_id: UUID of user
            role_id: New role ID
            is_tenant_admin: Whether user is tenant admin (None = no change)

        Returns:
            Updated tenant user dict or None if not found
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if is_tenant_admin is not None:
                    cursor.execute("""
                        UPDATE tenant_users
                        SET role_id = %s, is_tenant_admin = %s, updated_at = NOW()
                        WHERE tenant_id = %s AND user_id = %s
                        RETURNING *
                    """, (role_id, is_tenant_admin, tenant_id, user_id))
                else:
                    cursor.execute("""
                        UPDATE tenant_users
                        SET role_id = %s, updated_at = NOW()
                        WHERE tenant_id = %s AND user_id = %s
                        RETURNING *
                    """, (role_id, tenant_id, user_id))

                result = cursor.fetchone()
                if result:
                    logger.info(f"User {user_id} role updated in tenant {tenant_id}")
                    return dict(result)
                return None

        except Exception as e:
            logger.error(f"Failed to update user role: {e}")
            return None

    # =========================================================================
    # Invitation System
    # =========================================================================

    def create_invitation(
        self,
        tenant_id: str,
        email: str,
        role_id: int,
        invited_by: str,
        expires_in_days: int = 7
    ) -> Dict[str, Any]:
        """
        Create invitation to join tenant.

        Args:
            tenant_id: UUID of tenant
            email: Email address to invite
            role_id: Role ID to assign
            invited_by: User ID who created invitation
            expires_in_days: Expiration period

        Returns:
            Invitation dict with token

        Raises:
            TenantManagerException: If creation fails
        """
        try:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO tenant_invitations (
                        tenant_id, email, role_id, token, invited_by, expires_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (tenant_id, email, role_id, token, invited_by, expires_at))

                invitation = dict(cursor.fetchone())
                logger.info(f"Invitation created for {email} to tenant {tenant_id}")
                return invitation

        except Exception as e:
            raise TenantManagerException(f"Failed to create invitation: {e}")

    def accept_invitation(
        self,
        token: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Accept invitation and add user to tenant.

        Args:
            token: Invitation token
            user_id: User ID accepting invitation

        Returns:
            Tenant user mapping dict

        Raises:
            TenantManagerException: If acceptance fails
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get invitation
                cursor.execute("""
                    SELECT * FROM tenant_invitations
                    WHERE token = %s AND accepted_at IS NULL
                """, (token,))

                invitation = cursor.fetchone()

                if not invitation:
                    raise TenantManagerException("Invalid or already accepted invitation")

                if datetime.utcnow() > invitation['expires_at']:
                    raise TenantManagerException("Invitation has expired")

                # Add user to tenant
                result = self.add_user_to_tenant(
                    invitation['tenant_id'],
                    user_id,
                    invitation['role_id']
                )

                # Mark invitation as accepted
                cursor.execute("""
                    UPDATE tenant_invitations
                    SET accepted_at = NOW(), accepted_by = %s
                    WHERE id = %s
                """, (user_id, invitation['id']))

                logger.info(f"Invitation accepted: {token}")
                return result

        except TenantManagerException:
            raise
        except Exception as e:
            raise TenantManagerException(f"Failed to accept invitation: {e}")

    # =========================================================================
    # Quota Management
    # =========================================================================

    def check_device_quota(self, tenant_id: str) -> Dict[str, Any]:
        """
        Check device quota for tenant.

        Args:
            tenant_id: UUID of tenant

        Returns:
            Dict with quota information
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT check_tenant_device_quota(%s) as can_add
                """, (tenant_id,))

                can_add = cursor.fetchone()['can_add']

                cursor.execute("""
                    SELECT max_devices FROM tenants WHERE id = %s
                """, (tenant_id,))
                max_devices = cursor.fetchone()['max_devices']

                cursor.execute("""
                    SELECT COUNT(*) as current FROM devices WHERE tenant_id = %s
                """, (tenant_id,))
                current = cursor.fetchone()['current']

                return {
                    'can_add': can_add,
                    'current': current,
                    'max': max_devices,
                    'unlimited': max_devices is None,
                    'percentage': None if max_devices is None else (current / max_devices * 100)
                }

        except Exception as e:
            logger.error(f"Failed to check device quota: {e}")
            return {'can_add': False, 'error': str(e)}

    def check_user_quota(self, tenant_id: str) -> Dict[str, Any]:
        """
        Check user quota for tenant.

        Args:
            tenant_id: UUID of tenant

        Returns:
            Dict with quota information
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT check_tenant_user_quota(%s) as can_add
                """, (tenant_id,))

                can_add = cursor.fetchone()['can_add']

                cursor.execute("""
                    SELECT max_users FROM tenants WHERE id = %s
                """, (tenant_id,))
                max_users = cursor.fetchone()['max_users']

                cursor.execute("""
                    SELECT COUNT(*) as current FROM tenant_users WHERE tenant_id = %s
                """, (tenant_id,))
                current = cursor.fetchone()['current']

                return {
                    'can_add': can_add,
                    'current': current,
                    'max': max_users,
                    'unlimited': max_users is None,
                    'percentage': None if max_users is None else (current / max_users * 100)
                }

        except Exception as e:
            logger.error(f"Failed to check user quota: {e}")
            return {'can_add': False, 'error': str(e)}

    # =========================================================================
    # Statistics and Analytics
    # =========================================================================

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for tenant.

        Args:
            tenant_id: UUID of tenant

        Returns:
            Dict with tenant statistics
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM tenant_dashboard WHERE id = %s
                """, (tenant_id,))

                result = cursor.fetchone()
                return dict(result) if result else {}

        except Exception as e:
            logger.error(f"Failed to get tenant stats: {e}")
            return {}

    def get_all_tenant_stats(self) -> List[Dict[str, Any]]:
        """
        Get statistics for all tenants.

        Returns:
            List of tenant statistics dicts
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM tenant_dashboard ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get all tenant stats: {e}")
            return []


# =============================================================================
# Example usage
# =============================================================================

if __name__ == '__main__':
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'insa_iiot',
        'user': 'iiot_user',
        'password': 'iiot_secure_2025'
    }

    print("=== Tenant Manager Demo ===\n")

    with TenantManager(DB_CONFIG) as manager:
        # List all tenants
        tenants = manager.list_tenants()
        print(f"Total tenants: {len(tenants)}")

        for tenant in tenants:
            print(f"\nTenant: {tenant['name']}")
            print(f"  ID: {tenant['id']}")
            print(f"  Slug: {tenant['slug']}")
            print(f"  Status: {tenant['status']}")
            print(f"  Tier: {tenant['tier']}")

            # Get statistics
            stats = manager.get_tenant_stats(tenant['id'])
            print(f"  Devices: {stats.get('device_count', 0)}")
            print(f"  Users: {stats.get('user_count', 0)}")
            print(f"  Rules: {stats.get('rule_count', 0)}")
            print(f"  Alerts (24h): {stats.get('alerts_24h', 0)}")

            # Check quotas
            device_quota = manager.check_device_quota(tenant['id'])
            user_quota = manager.check_user_quota(tenant['id'])

            print(f"  Device Quota: {device_quota['current']}/{device_quota['max'] or '∞'}")
            print(f"  User Quota: {user_quota['current']}/{user_quota['max'] or '∞'}")

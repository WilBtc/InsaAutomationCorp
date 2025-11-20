"""
Tenant Management Service for Multi-Tenancy

This service handles all tenant-related operations including:
- CRUD operations for tenants
- Quota management
- User-tenant relationships
- Well-tenant assignments
- Tenant usage tracking
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from app.core.logging import get_logger
from app.core.exceptions import ValidationError, NotFoundError, ConflictError

logger = get_logger(__name__)


class TenantService:
    """Service for managing multi-tenant operations."""

    def __init__(self, db_pool):
        """
        Initialize tenant service.

        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool

    def _slugify(self, text: str) -> str:
        """
        Convert text to URL-friendly slug.

        Args:
            text: Text to slugify

        Returns:
            Slugified text

        Example:
            "Alkhorayef Petroleum" -> "alkhorayef-petroleum"
        """
        # Convert to lowercase
        slug = text.lower()
        # Remove special characters
        slug = re.sub(r'[^\w\s-]', '', slug)
        # Replace spaces with hyphens
        slug = re.sub(r'[-\s]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug

    def create_tenant(
        self,
        name: str,
        domain: Optional[str] = None,
        plan: str = 'standard',
        metadata: Optional[Dict[str, Any]] = None,
        custom_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new tenant with default quotas.

        Args:
            name: Tenant name (e.g., "Alkhorayef Petroleum")
            domain: Custom domain (optional)
            plan: Subscription plan (trial, standard, professional, enterprise)
            metadata: Additional metadata
            custom_slug: Custom slug (auto-generated if not provided)

        Returns:
            Created tenant dictionary

        Raises:
            ValidationError: If validation fails
            ConflictError: If tenant already exists
        """
        try:
            # Validate inputs
            if not name or len(name) < 2:
                raise ValidationError(
                    message="Tenant name must be at least 2 characters",
                    details={"field": "name", "value": name}
                )

            if plan not in ['trial', 'standard', 'professional', 'enterprise']:
                raise ValidationError(
                    message="Invalid plan",
                    details={
                        "field": "plan",
                        "value": plan,
                        "allowed": ['trial', 'standard', 'professional', 'enterprise']
                    }
                )

            # Generate or validate slug
            slug = custom_slug if custom_slug else self._slugify(name)

            if not re.match(r'^[a-z0-9-]+$', slug):
                raise ValidationError(
                    message="Slug must contain only lowercase letters, numbers, and hyphens",
                    details={"field": "slug", "value": slug}
                )

            # Check if tenant already exists
            existing = self.db_pool.execute_query(
                "SELECT id FROM tenants WHERE slug = %s OR (domain = %s AND domain IS NOT NULL)",
                (slug, domain),
                fetch=True
            )

            if existing:
                raise ConflictError(
                    message="Tenant with this slug or domain already exists",
                    details={"slug": slug, "domain": domain}
                )

            # Use database function to create tenant with quotas
            result = self.db_pool.execute_query(
                "SELECT create_tenant(%s, %s, %s, %s, %s) AS tenant_id",
                (name, slug, domain, plan, metadata or {}),
                fetch=True
            )

            tenant_id = result[0][0] if result else None

            if not tenant_id:
                raise Exception("Failed to create tenant")

            logger.info(
                f"Created tenant: {name} (ID: {tenant_id}, slug: {slug}, plan: {plan})",
                extra={
                    "extra_fields": {
                        "tenant_id": tenant_id,
                        "tenant_name": name,
                        "tenant_slug": slug,
                        "plan": plan
                    }
                }
            )

            # Retrieve the created tenant
            return self.get_tenant(tenant_id)

        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}", exc_info=e)
            raise Exception(f"Failed to create tenant: {str(e)}")

    def get_tenant(self, tenant_id: int) -> Dict[str, Any]:
        """
        Get tenant by ID.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant dictionary

        Raises:
            NotFoundError: If tenant not found
        """
        try:
            result = self.db_pool.execute_query(
                """
                SELECT
                    t.id,
                    t.name,
                    t.slug,
                    t.domain,
                    t.status,
                    t.plan,
                    t.created_at,
                    t.updated_at,
                    t.activated_at,
                    t.suspended_at,
                    t.metadata,
                    t.settings,
                    q.api_calls_per_hour,
                    q.api_calls_per_day,
                    q.api_burst_limit,
                    q.storage_gb,
                    q.max_wells,
                    q.max_users,
                    q.retention_days,
                    q.backup_retention_days,
                    q.features,
                    (SELECT COUNT(*) FROM tenant_users WHERE tenant_id = t.id) AS user_count,
                    (SELECT COUNT(*) FROM tenant_wells WHERE tenant_id = t.id AND status = 'active') AS well_count
                FROM tenants t
                LEFT JOIN tenant_quotas q ON q.tenant_id = t.id
                WHERE t.id = %s
                """,
                (tenant_id,),
                fetch=True
            )

            if not result:
                raise NotFoundError(
                    message=f"Tenant not found",
                    details={"tenant_id": tenant_id}
                )

            row = result[0]
            return {
                "id": row[0],
                "name": row[1],
                "slug": row[2],
                "domain": row[3],
                "status": row[4],
                "plan": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "updated_at": row[7].isoformat() if row[7] else None,
                "activated_at": row[8].isoformat() if row[8] else None,
                "suspended_at": row[9].isoformat() if row[9] else None,
                "metadata": row[10],
                "settings": row[11],
                "quotas": {
                    "api_calls_per_hour": row[12],
                    "api_calls_per_day": row[13],
                    "api_burst_limit": row[14],
                    "storage_gb": row[15],
                    "max_wells": row[16],
                    "max_users": row[17],
                    "retention_days": row[18],
                    "backup_retention_days": row[19],
                    "features": row[20]
                } if row[12] is not None else None,
                "stats": {
                    "user_count": row[21],
                    "well_count": row[22]
                }
            }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}", exc_info=e)
            raise Exception(f"Failed to get tenant: {str(e)}")

    def get_tenant_by_slug(self, slug: str) -> Dict[str, Any]:
        """
        Get tenant by slug.

        Args:
            slug: Tenant slug

        Returns:
            Tenant dictionary

        Raises:
            NotFoundError: If tenant not found
        """
        try:
            result = self.db_pool.execute_query(
                "SELECT id FROM tenants WHERE slug = %s",
                (slug,),
                fetch=True
            )

            if not result:
                raise NotFoundError(
                    message=f"Tenant not found",
                    details={"slug": slug}
                )

            tenant_id = result[0][0]
            return self.get_tenant(tenant_id)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get tenant by slug {slug}: {e}", exc_info=e)
            raise Exception(f"Failed to get tenant: {str(e)}")

    def list_tenants(
        self,
        status: Optional[str] = None,
        plan: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List tenants with optional filtering.

        Args:
            status: Filter by status
            plan: Filter by plan
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            Tuple of (tenants list, total count)
        """
        try:
            # Build WHERE clause
            where_clauses = []
            params = []

            if status:
                where_clauses.append("t.status = %s")
                params.append(status)

            if plan:
                where_clauses.append("t.plan = %s")
                params.append(plan)

            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Get total count
            count_result = self.db_pool.execute_query(
                f"SELECT COUNT(*) FROM tenants t {where_sql}",
                tuple(params),
                fetch=True
            )
            total = count_result[0][0] if count_result else 0

            # Get tenants
            params.extend([limit, offset])
            result = self.db_pool.execute_query(
                f"""
                SELECT
                    t.id,
                    t.name,
                    t.slug,
                    t.domain,
                    t.status,
                    t.plan,
                    t.created_at,
                    (SELECT COUNT(*) FROM tenant_users WHERE tenant_id = t.id) AS user_count,
                    (SELECT COUNT(*) FROM tenant_wells WHERE tenant_id = t.id AND status = 'active') AS well_count
                FROM tenants t
                {where_sql}
                ORDER BY t.created_at DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params),
                fetch=True
            )

            tenants = []
            for row in result:
                tenants.append({
                    "id": row[0],
                    "name": row[1],
                    "slug": row[2],
                    "domain": row[3],
                    "status": row[4],
                    "plan": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "user_count": row[7],
                    "well_count": row[8]
                })

            return tenants, total

        except Exception as e:
            logger.error(f"Failed to list tenants: {e}", exc_info=e)
            raise Exception(f"Failed to list tenants: {str(e)}")

    def update_tenant(
        self,
        tenant_id: int,
        name: Optional[str] = None,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        plan: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update tenant details.

        Args:
            tenant_id: Tenant ID
            name: New name (optional)
            domain: New domain (optional)
            status: New status (optional)
            plan: New plan (optional)
            metadata: Updated metadata (optional)
            settings: Updated settings (optional)

        Returns:
            Updated tenant dictionary

        Raises:
            NotFoundError: If tenant not found
            ValidationError: If validation fails
        """
        try:
            # Verify tenant exists
            self.get_tenant(tenant_id)

            # Build UPDATE statement
            updates = []
            params = []

            if name is not None:
                if len(name) < 2:
                    raise ValidationError(
                        message="Tenant name must be at least 2 characters",
                        details={"field": "name", "value": name}
                    )
                updates.append("name = %s")
                params.append(name)

            if domain is not None:
                updates.append("domain = %s")
                params.append(domain)

            if status is not None:
                if status not in ['active', 'suspended', 'inactive', 'trial']:
                    raise ValidationError(
                        message="Invalid status",
                        details={"field": "status", "value": status}
                    )
                updates.append("status = %s")
                params.append(status)

                # Update suspended_at if status changes
                if status == 'suspended':
                    updates.append("suspended_at = NOW()")

            if plan is not None:
                if plan not in ['trial', 'standard', 'professional', 'enterprise']:
                    raise ValidationError(
                        message="Invalid plan",
                        details={"field": "plan", "value": plan}
                    )
                updates.append("plan = %s")
                params.append(plan)

            if metadata is not None:
                updates.append("metadata = %s")
                params.append(metadata)

            if settings is not None:
                updates.append("settings = %s")
                params.append(settings)

            if not updates:
                # Nothing to update
                return self.get_tenant(tenant_id)

            # Add tenant_id to params
            params.append(tenant_id)

            # Execute update
            self.db_pool.execute_query(
                f"""
                UPDATE tenants
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE id = %s
                """,
                tuple(params),
                fetch=False
            )

            logger.info(
                f"Updated tenant {tenant_id}",
                extra={
                    "extra_fields": {
                        "tenant_id": tenant_id,
                        "updates": updates
                    }
                }
            )

            return self.get_tenant(tenant_id)

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {e}", exc_info=e)
            raise Exception(f"Failed to update tenant: {str(e)}")

    def update_quota(
        self,
        tenant_id: int,
        api_calls_per_hour: Optional[int] = None,
        api_calls_per_day: Optional[int] = None,
        storage_gb: Optional[int] = None,
        max_wells: Optional[int] = None,
        max_users: Optional[int] = None,
        retention_days: Optional[int] = None,
        features: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Update tenant quotas.

        Args:
            tenant_id: Tenant ID
            api_calls_per_hour: API calls per hour limit
            api_calls_per_day: API calls per day limit
            storage_gb: Storage limit in GB
            max_wells: Maximum wells
            max_users: Maximum users
            retention_days: Data retention days
            features: Feature flags

        Returns:
            Updated tenant dictionary

        Raises:
            NotFoundError: If tenant not found
            ValidationError: If validation fails
        """
        try:
            # Verify tenant exists
            self.get_tenant(tenant_id)

            # Build UPDATE statement
            updates = []
            params = []

            if api_calls_per_hour is not None:
                if api_calls_per_hour <= 0:
                    raise ValidationError(
                        message="API calls per hour must be positive",
                        details={"field": "api_calls_per_hour", "value": api_calls_per_hour}
                    )
                updates.append("api_calls_per_hour = %s")
                params.append(api_calls_per_hour)

            if api_calls_per_day is not None:
                if api_calls_per_day <= 0:
                    raise ValidationError(
                        message="API calls per day must be positive",
                        details={"field": "api_calls_per_day", "value": api_calls_per_day}
                    )
                updates.append("api_calls_per_day = %s")
                params.append(api_calls_per_day)

            if storage_gb is not None:
                if storage_gb <= 0:
                    raise ValidationError(
                        message="Storage GB must be positive",
                        details={"field": "storage_gb", "value": storage_gb}
                    )
                updates.append("storage_gb = %s")
                params.append(storage_gb)

            if max_wells is not None:
                if max_wells <= 0:
                    raise ValidationError(
                        message="Max wells must be positive",
                        details={"field": "max_wells", "value": max_wells}
                    )
                updates.append("max_wells = %s")
                params.append(max_wells)

            if max_users is not None:
                if max_users <= 0:
                    raise ValidationError(
                        message="Max users must be positive",
                        details={"field": "max_users", "value": max_users}
                    )
                updates.append("max_users = %s")
                params.append(max_users)

            if retention_days is not None:
                if retention_days <= 0:
                    raise ValidationError(
                        message="Retention days must be positive",
                        details={"field": "retention_days", "value": retention_days}
                    )
                updates.append("retention_days = %s")
                params.append(retention_days)

            if features is not None:
                updates.append("features = %s")
                params.append(features)

            if not updates:
                # Nothing to update
                return self.get_tenant(tenant_id)

            # Add tenant_id to params
            params.append(tenant_id)

            # Execute update
            self.db_pool.execute_query(
                f"""
                UPDATE tenant_quotas
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE tenant_id = %s
                """,
                tuple(params),
                fetch=False
            )

            logger.info(
                f"Updated quotas for tenant {tenant_id}",
                extra={
                    "extra_fields": {
                        "tenant_id": tenant_id,
                        "updates": updates
                    }
                }
            )

            return self.get_tenant(tenant_id)

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update quotas for tenant {tenant_id}: {e}", exc_info=e)
            raise Exception(f"Failed to update quotas: {str(e)}")

    def add_user_to_tenant(
        self,
        tenant_id: int,
        user_id: int,
        role: str = 'viewer',
        is_primary: bool = False,
        invited_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add a user to a tenant.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            role: User role within tenant (admin, operator, viewer)
            is_primary: Whether this is the primary contact
            invited_by: User ID who invited this user

        Returns:
            Tenant-user relationship dictionary

        Raises:
            NotFoundError: If tenant or user not found
            ConflictError: If user already in tenant
            ValidationError: If quota exceeded
        """
        try:
            # Verify tenant exists
            tenant = self.get_tenant(tenant_id)

            # Check user count quota
            if tenant['stats']['user_count'] >= tenant['quotas']['max_users']:
                raise ValidationError(
                    message="User quota exceeded",
                    details={
                        "current": tenant['stats']['user_count'],
                        "max": tenant['quotas']['max_users']
                    }
                )

            # Check if user already in tenant
            existing = self.db_pool.execute_query(
                "SELECT id FROM tenant_users WHERE tenant_id = %s AND user_id = %s",
                (tenant_id, user_id),
                fetch=True
            )

            if existing:
                raise ConflictError(
                    message="User already in tenant",
                    details={"tenant_id": tenant_id, "user_id": user_id}
                )

            # Validate role
            if role not in ['admin', 'operator', 'viewer']:
                raise ValidationError(
                    message="Invalid role",
                    details={"field": "role", "value": role, "allowed": ['admin', 'operator', 'viewer']}
                )

            # Add user to tenant
            result = self.db_pool.execute_query(
                """
                INSERT INTO tenant_users (tenant_id, user_id, role, is_primary, invited_by, joined_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                RETURNING id, joined_at
                """,
                (tenant_id, user_id, role, is_primary, invited_by),
                fetch=True
            )

            relationship_id = result[0][0]
            joined_at = result[0][1]

            # Also update users table tenant_id (primary tenant)
            self.db_pool.execute_query(
                "UPDATE users SET tenant_id = %s WHERE id = %s AND tenant_id IS NULL",
                (tenant_id, user_id),
                fetch=False
            )

            logger.info(
                f"Added user {user_id} to tenant {tenant_id} with role {role}",
                extra={
                    "extra_fields": {
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "role": role,
                        "is_primary": is_primary
                    }
                }
            )

            return {
                "id": relationship_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "role": role,
                "is_primary": is_primary,
                "joined_at": joined_at.isoformat() if joined_at else None,
                "invited_by": invited_by
            }

        except (NotFoundError, ConflictError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to add user to tenant: {e}", exc_info=e)
            raise Exception(f"Failed to add user to tenant: {str(e)}")

    def get_tenant_usage(self, tenant_id: int, period_hours: int = 24) -> Dict[str, Any]:
        """
        Get current usage statistics for a tenant.

        Args:
            tenant_id: Tenant ID
            period_hours: Time period in hours (default: 24)

        Returns:
            Usage statistics dictionary

        Raises:
            NotFoundError: If tenant not found
        """
        try:
            # Verify tenant exists
            tenant = self.get_tenant(tenant_id)

            # Get usage from database function
            result = self.db_pool.execute_query(
                "SELECT * FROM get_tenant_usage(%s, %s)",
                (tenant_id, period_hours),
                fetch=True
            )

            usage = {}
            for row in result:
                metric = row[0]
                usage[metric] = {
                    "current": row[1],
                    "limit": row[2],
                    "percent": float(row[3]) if row[3] else 0
                }

            return {
                "tenant_id": tenant_id,
                "tenant_name": tenant['name'],
                "period_hours": period_hours,
                "usage": usage,
                "timestamp": datetime.utcnow().isoformat()
            }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get usage for tenant {tenant_id}: {e}", exc_info=e)
            raise Exception(f"Failed to get tenant usage: {str(e)}")

    def assign_well_to_tenant(
        self,
        tenant_id: int,
        well_id: str,
        well_name: Optional[str] = None,
        location: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assign a well to a tenant.

        Args:
            tenant_id: Tenant ID
            well_id: Well unique identifier
            well_name: Well name
            location: Well location
            metadata: Additional metadata

        Returns:
            Well assignment dictionary

        Raises:
            NotFoundError: If tenant not found
            ConflictError: If well already assigned
            ValidationError: If quota exceeded
        """
        try:
            # Verify tenant exists
            tenant = self.get_tenant(tenant_id)

            # Check well quota
            if tenant['stats']['well_count'] >= tenant['quotas']['max_wells']:
                raise ValidationError(
                    message="Well quota exceeded",
                    details={
                        "current": tenant['stats']['well_count'],
                        "max": tenant['quotas']['max_wells']
                    }
                )

            # Check if well already assigned
            existing = self.db_pool.execute_query(
                "SELECT id FROM tenant_wells WHERE tenant_id = %s AND well_id = %s",
                (tenant_id, well_id),
                fetch=True
            )

            if existing:
                raise ConflictError(
                    message="Well already assigned to this tenant",
                    details={"tenant_id": tenant_id, "well_id": well_id}
                )

            # Assign well
            result = self.db_pool.execute_query(
                """
                INSERT INTO tenant_wells (tenant_id, well_id, well_name, location, status, added_at, metadata)
                VALUES (%s, %s, %s, %s, 'active', NOW(), %s)
                RETURNING id, added_at
                """,
                (tenant_id, well_id, well_name, location, metadata or {}),
                fetch=True
            )

            assignment_id = result[0][0]
            added_at = result[0][1]

            logger.info(
                f"Assigned well {well_id} to tenant {tenant_id}",
                extra={
                    "extra_fields": {
                        "tenant_id": tenant_id,
                        "well_id": well_id,
                        "well_name": well_name
                    }
                }
            )

            return {
                "id": assignment_id,
                "tenant_id": tenant_id,
                "well_id": well_id,
                "well_name": well_name,
                "location": location,
                "status": "active",
                "added_at": added_at.isoformat() if added_at else None,
                "metadata": metadata or {}
            }

        except (NotFoundError, ConflictError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to assign well to tenant: {e}", exc_info=e)
            raise Exception(f"Failed to assign well: {str(e)}")

    def check_feature_access(self, tenant_id: int, feature: str) -> bool:
        """
        Check if tenant has access to a specific feature.

        Args:
            tenant_id: Tenant ID
            feature: Feature name

        Returns:
            True if tenant has access, False otherwise
        """
        try:
            result = self.db_pool.execute_query(
                "SELECT features FROM tenant_quotas WHERE tenant_id = %s",
                (tenant_id,),
                fetch=True
            )

            if not result or not result[0][0]:
                return False

            features = result[0][0]
            return features.get(feature, False)

        except Exception as e:
            logger.error(f"Failed to check feature access: {e}", exc_info=e)
            return False

"""
Tenant Management API Routes

This module provides RESTful endpoints for tenant management:
- CRUD operations for tenants
- Quota management
- User-tenant relationships
- Well assignments
- Usage tracking
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any
from app.core.auth import require_auth, UserRole
from app.core.logging import get_logger
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    QuotaExceededError
)
from app.middleware.tenant_middleware import require_super_admin, require_tenant
from app.services.tenant_service import TenantService
from app.services.quota_service import QuotaService
from app.db.pool import get_db_pool

logger = get_logger(__name__)

# Create Blueprint
tenants_bp = Blueprint('tenants', __name__, url_prefix='/api/v1/tenants')


def get_tenant_service() -> TenantService:
    """Get tenant service instance."""
    db_pool = get_db_pool()
    return TenantService(db_pool)


def get_quota_service() -> QuotaService:
    """Get quota service instance."""
    db_pool = get_db_pool()
    return QuotaService(db_pool)


# ============================================================================
# Tenant CRUD Operations
# ============================================================================

@tenants_bp.route('', methods=['POST'])
@require_auth()
@require_super_admin()
def create_tenant():
    """
    Create a new tenant (super-admin only).

    Request body:
        {
            "name": "Alkhorayef Petroleum",
            "domain": "alkhorayef.example.com",  # optional
            "plan": "enterprise",  # trial, standard, professional, enterprise
            "metadata": {...}  # optional
        }

    Returns:
        201: Tenant created successfully
        400: Validation error
        403: Forbidden (not super-admin)
        409: Conflict (tenant already exists)
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "validation_error",
                "message": "Request body is required"
            }), 400

        # Validate required fields
        name = data.get('name')
        if not name:
            return jsonify({
                "error": "validation_error",
                "message": "Tenant name is required",
                "field": "name"
            }), 400

        # Optional fields
        domain = data.get('domain')
        plan = data.get('plan', 'standard')
        metadata = data.get('metadata', {})
        custom_slug = data.get('slug')

        # Create tenant
        tenant_service = get_tenant_service()
        tenant = tenant_service.create_tenant(
            name=name,
            domain=domain,
            plan=plan,
            metadata=metadata,
            custom_slug=custom_slug
        )

        logger.info(
            f"Tenant created: {tenant['name']} (ID: {tenant['id']})",
            extra={
                "extra_fields": {
                    "tenant_id": tenant['id'],
                    "created_by": g.current_user.get('username')
                }
            }
        )

        return jsonify({
            "success": True,
            "message": "Tenant created successfully",
            "tenant": tenant
        }), 201

    except ValidationError as e:
        return jsonify({
            "error": "validation_error",
            "message": e.message,
            "details": e.details
        }), 400
    except ConflictError as e:
        return jsonify({
            "error": "conflict",
            "message": e.message,
            "details": e.details
        }), 409
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}", exc_info=e)
        return jsonify({
            "error": "internal_error",
            "message": "Failed to create tenant"
        }), 500


@tenants_bp.route('', methods=['GET'])
@require_auth()
@require_super_admin()
def list_tenants():
    """
    List all tenants (super-admin only).

    Query parameters:
        - status: Filter by status (active, suspended, inactive, trial)
        - plan: Filter by plan (trial, standard, professional, enterprise)
        - limit: Max results (default: 100)
        - offset: Pagination offset (default: 0)

    Returns:
        200: Tenant list
        403: Forbidden (not super-admin)
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        plan = request.args.get('plan')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        # Validate limits
        if limit > 1000:
            limit = 1000
        if limit < 1:
            limit = 1

        # Get tenants
        tenant_service = get_tenant_service()
        tenants, total = tenant_service.list_tenants(
            status=status,
            plan=plan,
            limit=limit,
            offset=offset
        )

        return jsonify({
            "success": True,
            "tenants": tenants,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "count": len(tenants)
            }
        }), 200

    except Exception as e:
        logger.error(f"Failed to list tenants: {e}", exc_info=e)
        return jsonify({
            "error": "internal_error",
            "message": "Failed to list tenants"
        }), 500


@tenants_bp.route('/<int:tenant_id>', methods=['GET'])
@require_auth()
def get_tenant(tenant_id: int):
    """
    Get tenant details.

    Super-admins can view any tenant.
    Regular users can only view their own tenant.

    Path parameters:
        tenant_id: Tenant ID

    Returns:
        200: Tenant details
        403: Forbidden
        404: Tenant not found
    """
    try:
        # Check permissions
        is_super_admin = g.current_user.get('is_super_admin', False)
        user_tenant_id = g.current_user.get('tenant_id')

        if not is_super_admin and user_tenant_id != tenant_id:
            return jsonify({
                "error": "forbidden",
                "message": "You can only view your own tenant"
            }), 403

        # Get tenant
        tenant_service = get_tenant_service()
        tenant = tenant_service.get_tenant(tenant_id)

        return jsonify({
            "success": True,
            "tenant": tenant
        }), 200

    except NotFoundError as e:
        return jsonify({
            "error": "not_found",
            "message": e.message,
            "details": e.details
        }), 404
    except Exception as e:
        logger.error(f"Failed to get tenant: {e}", exc_info=e)
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get tenant"
        }), 500


@tenants_bp.route('/<int:tenant_id>', methods=['PUT'])
@require_auth()
def update_tenant(tenant_id: int):
    """
    Update tenant details.

    Super-admins can update any tenant.
    Tenant admins can update their own tenant (limited fields).

    Path parameters:
        tenant_id: Tenant ID

    Request body:
        {
            "name": "New Name",
            "domain": "new-domain.com",
            "status": "active",  # super-admin only
            "plan": "enterprise",  # super-admin only
            "metadata": {...},
            "settings": {...}
        }

    Returns:
        200: Tenant updated
        400: Validation error
        403: Forbidden
        404: Tenant not found
    """
    try:
        # Check permissions
        is_super_admin = g.current_user.get('is_super_admin', False)
        user_tenant_id = g.current_user.get('tenant_id')
        user_role = g.current_user.get('role')

        if not is_super_admin and user_tenant_id != tenant_id:
            return jsonify({
                "error": "forbidden",
                "message": "You can only update your own tenant"
            }), 403

        if not is_super_admin and user_role != UserRole.ADMIN.value:
            return jsonify({
                "error": "forbidden",
                "message": "Only tenant admins can update tenant details"
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "error": "validation_error",
                "message": "Request body is required"
            }), 400

        # Fields that tenant admins can update
        allowed_fields = ['name', 'metadata', 'settings']

        # Additional fields for super-admins
        if is_super_admin:
            allowed_fields.extend(['domain', 'status', 'plan'])

        # Filter to allowed fields
        updates = {k: v for k, v in data.items() if k in allowed_fields}

        if not updates:
            return jsonify({
                "error": "validation_error",
                "message": "No valid fields to update"
            }), 400

        # Update tenant
        tenant_service = get_tenant_service()
        tenant = tenant_service.update_tenant(tenant_id, **updates)

        logger.info(
            f"Tenant {tenant_id} updated",
            extra={
                "extra_fields": {
                    "tenant_id": tenant_id,
                    "updated_by": g.current_user.get('username'),
                    "fields": list(updates.keys())
                }
            }
        )

        return jsonify({
            "success": True,
            "message": "Tenant updated successfully",
            "tenant": tenant
        }), 200

    except ValidationError as e:
        return jsonify({
            "error": "validation_error",
            "message": e.message,
            "details": e.details
        }), 400
    except NotFoundError as e:
        return jsonify({
            "error": "not_found",
            "message": e.message,
            "details": e.details
        }), 404
    except Exception as e:
        logger.error(f"Failed to update tenant: {e}", exc_info=e)
        return jsonify({
            "error": "internal_error",
            "message": "Failed to update tenant"
        }), 500


# ============================================================================
# Quota Management
# ============================================================================

@tenants_bp.route('/<int:tenant_id>/quotas', methods=['GET'])
@require_auth()
def get_tenant_quotas(tenant_id: int):
    """
    Get tenant quotas.

    Path parameters:
        tenant_id: Tenant ID

    Returns:
        200: Quota information
        403: Forbidden
        404: Tenant not found
    """
    try:
        # Check permissions
        is_super_admin = g.current_user.get('is_super_admin', False)
        user_tenant_id = g.current_user.get('tenant_id')

        if not is_super_admin and user_tenant_id != tenant_id:
            return jsonify({
                "error": "forbidden",
                "message": "You can only view your own quotas"
            }), 403

        # Get tenant (includes quotas)
        tenant_service = get_tenant_service()
        tenant = tenant_service.get_tenant(tenant_id)

        # Get current quota status
        quota_service = get_quota_service()
        quota_status = quota_service.get_quota_status(tenant_id)

        return jsonify({
            "success": True,
            "quotas": tenant.get('quotas'),
            "current_usage": quota_status
        }), 200

    except NotFoundError as e:
        return jsonify({
            "error": "not_found",
            "message": e.message,
            "details": e.details
        }), 404
    except Exception as e:
        logger.error(f"Failed to get quotas: {e}", exc_info=e)
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get quotas"
        }), 500


@tenants_bp.route('/<int:tenant_id>/quotas', methods=['PUT'])
@require_auth()
@require_super_admin()
def update_tenant_quotas(tenant_id: int):
    """
    Update tenant quotas (super-admin only).

    Path parameters:
        tenant_id: Tenant ID

    Request body:
        {
            "api_calls_per_hour": 20000,
            "api_calls_per_day": 400000,
            "storage_gb": 200,
            "max_wells": 100,
            "max_users": 20,
            "retention_days": 60,
            "features": {
                "advanced_analytics": true,
                "ml_predictions": true,
                ...
            }
        }

    Returns:
        200: Quotas updated
        400: Validation error
        403: Forbidden
        404: Tenant not found
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "validation_error",
                "message": "Request body is required"
            }), 400

        # Update quotas
        tenant_service = get_tenant_service()
        tenant = tenant_service.update_quota(tenant_id, **data)

        logger.info(
            f"Quotas updated for tenant {tenant_id}",
            extra={
                "extra_fields": {
                    "tenant_id": tenant_id,
                    "updated_by": g.current_user.get('username'),
                    "fields": list(data.keys())
                }
            }
        )

        return jsonify({
            "success": True,
            "message": "Quotas updated successfully",
            "tenant": tenant
        }), 200

    except ValidationError as e:
        return jsonify({
            "error": "validation_error",
            "message": e.message,
            "details": e.details
        }), 400
    except NotFoundError as e:
        return jsonify({
            "error": "not_found",
            "message": e.message,
            "details": e.details
        }), 404
    except Exception as e:
        logger.error(f"Failed to update quotas: {e}", exc_info=e)
        return jsonify({
            "error": "internal_error",
            "message": "Failed to update quotas"
        }), 500


@tenants_bp.route('/<int:tenant_id>/usage', methods=['GET'])
@require_auth()
def get_tenant_usage(tenant_id: int):
    """
    Get tenant usage statistics.

    Path parameters:
        tenant_id: Tenant ID

    Query parameters:
        period_hours: Time period in hours (default: 24)

    Returns:
        200: Usage statistics
        403: Forbidden
        404: Tenant not found
    """
    try:
        # Check permissions
        is_super_admin = g.current_user.get('is_super_admin', False)
        user_tenant_id = g.current_user.get('tenant_id')

        if not is_super_admin and user_tenant_id != tenant_id:
            return jsonify({
                "error": "forbidden",
                "message": "You can only view your own usage"
            }), 403

        # Get period
        period_hours = int(request.args.get('period_hours', 24))

        # Get usage
        tenant_service = get_tenant_service()
        usage = tenant_service.get_tenant_usage(tenant_id, period_hours)

        return jsonify({
            "success": True,
            "usage": usage
        }), 200

    except NotFoundError as e:
        return jsonify({
            "error": "not_found",
            "message": e.message,
            "details": e.details
        }), 404
    except Exception as e:
        logger.error(f"Failed to get usage: {e}", exc_info=e)
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get usage"
        }), 500


# ============================================================================
# User-Tenant Management
# ============================================================================

@tenants_bp.route('/<int:tenant_id>/users', methods=['POST'])
@require_auth()
def add_user_to_tenant(tenant_id: int):
    """
    Add a user to a tenant.

    Only tenant admins or super-admins can add users.

    Path parameters:
        tenant_id: Tenant ID

    Request body:
        {
            "user_id": 123,
            "role": "operator",  # admin, operator, viewer
            "is_primary": false
        }

    Returns:
        201: User added
        400: Validation error
        403: Forbidden
        404: Not found
        409: User already in tenant
    """
    try:
        # Check permissions
        is_super_admin = g.current_user.get('is_super_admin', False)
        user_tenant_id = g.current_user.get('tenant_id')
        user_role = g.current_user.get('role')

        if not is_super_admin and user_tenant_id != tenant_id:
            return jsonify({
                "error": "forbidden",
                "message": "You can only add users to your own tenant"
            }), 403

        if not is_super_admin and user_role != UserRole.ADMIN.value:
            return jsonify({
                "error": "forbidden",
                "message": "Only tenant admins can add users"
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "error": "validation_error",
                "message": "Request body is required"
            }), 400

        user_id = data.get('user_id')
        if not user_id:
            return jsonify({
                "error": "validation_error",
                "message": "user_id is required"
            }), 400

        role = data.get('role', 'viewer')
        is_primary = data.get('is_primary', False)

        # Add user to tenant
        tenant_service = get_tenant_service()
        relationship = tenant_service.add_user_to_tenant(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            is_primary=is_primary,
            invited_by=g.current_user.get('user_id')
        )

        logger.info(
            f"User {user_id} added to tenant {tenant_id}",
            extra={
                "extra_fields": {
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "role": role,
                    "added_by": g.current_user.get('username')
                }
            }
        )

        return jsonify({
            "success": True,
            "message": "User added to tenant successfully",
            "relationship": relationship
        }), 201

    except ValidationError as e:
        return jsonify({
            "error": "validation_error",
            "message": e.message,
            "details": e.details
        }), 400
    except ConflictError as e:
        return jsonify({
            "error": "conflict",
            "message": e.message,
            "details": e.details
        }), 409
    except NotFoundError as e:
        return jsonify({
            "error": "not_found",
            "message": e.message,
            "details": e.details
        }), 404
    except Exception as e:
        logger.error(f"Failed to add user to tenant: {e}", exc_info=e)
        return jsonify({
            "error": "internal_error",
            "message": "Failed to add user to tenant"
        }), 500


# ============================================================================
# Well-Tenant Management
# ============================================================================

@tenants_bp.route('/<int:tenant_id>/wells', methods=['POST'])
@require_auth()
def assign_well_to_tenant(tenant_id: int):
    """
    Assign a well to a tenant.

    Only tenant admins or super-admins can assign wells.

    Path parameters:
        tenant_id: Tenant ID

    Request body:
        {
            "well_id": "WELL-001",
            "well_name": "North Field A1",
            "location": "North Field",
            "metadata": {...}
        }

    Returns:
        201: Well assigned
        400: Validation error
        403: Forbidden
        404: Not found
        409: Well already assigned
    """
    try:
        # Check permissions
        is_super_admin = g.current_user.get('is_super_admin', False)
        user_tenant_id = g.current_user.get('tenant_id')
        user_role = g.current_user.get('role')

        if not is_super_admin and user_tenant_id != tenant_id:
            return jsonify({
                "error": "forbidden",
                "message": "You can only assign wells to your own tenant"
            }), 403

        if not is_super_admin and user_role != UserRole.ADMIN.value:
            return jsonify({
                "error": "forbidden",
                "message": "Only tenant admins can assign wells"
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "error": "validation_error",
                "message": "Request body is required"
            }), 400

        well_id = data.get('well_id')
        if not well_id:
            return jsonify({
                "error": "validation_error",
                "message": "well_id is required"
            }), 400

        well_name = data.get('well_name')
        location = data.get('location')
        metadata = data.get('metadata', {})

        # Assign well
        tenant_service = get_tenant_service()
        assignment = tenant_service.assign_well_to_tenant(
            tenant_id=tenant_id,
            well_id=well_id,
            well_name=well_name,
            location=location,
            metadata=metadata
        )

        logger.info(
            f"Well {well_id} assigned to tenant {tenant_id}",
            extra={
                "extra_fields": {
                    "tenant_id": tenant_id,
                    "well_id": well_id,
                    "assigned_by": g.current_user.get('username')
                }
            }
        )

        return jsonify({
            "success": True,
            "message": "Well assigned to tenant successfully",
            "assignment": assignment
        }), 201

    except ValidationError as e:
        return jsonify({
            "error": "validation_error",
            "message": e.message,
            "details": e.details
        }), 400
    except ConflictError as e:
        return jsonify({
            "error": "conflict",
            "message": e.message,
            "details": e.details
        }), 409
    except NotFoundError as e:
        return jsonify({
            "error": "not_found",
            "message": e.message,
            "details": e.details
        }), 404
    except Exception as e:
        logger.error(f"Failed to assign well: {e}", exc_info=e)
        return jsonify({
            "error": "internal_error",
            "message": "Failed to assign well"
        }), 500

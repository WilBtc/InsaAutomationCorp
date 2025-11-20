"""
Tenant Middleware for Multi-Tenancy

This middleware:
1. Extracts tenant context from JWT token
2. Attaches tenant info to request (g.tenant)
3. Sets PostgreSQL session variables for RLS
4. Checks quota limits before processing requests
5. Decrements concurrent counter after request completes
"""

from functools import wraps
from flask import request, g, jsonify
from typing import Optional, Callable
from app.core.logging import get_logger
from app.core.auth import decode_token, get_token_from_request
from app.core.exceptions import AuthenticationError, QuotaExceededError
from app.services.quota_service import QuotaService

logger = get_logger(__name__)


class TenantMiddleware:
    """Middleware for tenant context and quota enforcement."""

    def __init__(self, app=None, db_pool=None, quota_service: Optional[QuotaService] = None):
        """
        Initialize tenant middleware.

        Args:
            app: Flask application instance
            db_pool: Database connection pool
            quota_service: Quota service instance (optional)
        """
        self.db_pool = db_pool
        self.quota_service = quota_service

        if app and db_pool:
            self.init_app(app, db_pool, quota_service)

    def init_app(self, app, db_pool, quota_service: Optional[QuotaService] = None):
        """
        Initialize middleware with Flask app.

        Args:
            app: Flask application instance
            db_pool: Database connection pool
            quota_service: Quota service instance (optional)
        """
        self.db_pool = db_pool
        self.quota_service = quota_service or QuotaService(db_pool)

        # Register before_request handler
        app.before_request(self.before_request)

        # Register after_request handler
        app.after_request(self.after_request)

        # Register teardown handler
        app.teardown_request(self.teardown_request)

        logger.info("Tenant middleware initialized")

    def before_request(self):
        """
        Process request before routing.

        Extracts tenant from JWT and sets context.
        """
        # Skip for health checks and public endpoints
        if self._is_public_endpoint():
            return None

        try:
            # Extract token
            token = get_token_from_request()

            if not token:
                # No token - allow through (auth decorator will handle)
                return None

            # Decode token
            try:
                payload = decode_token(token)
            except AuthenticationError:
                # Invalid token - allow through (auth decorator will handle)
                return None

            # Extract tenant information
            tenant_id = payload.get('tenant_id')
            is_super_admin = payload.get('is_super_admin', False)
            user_id = payload.get('user_id')

            # Store tenant context in g
            g.tenant_id = tenant_id
            g.is_super_admin = is_super_admin
            g.user_id = user_id

            # Set PostgreSQL session variables for RLS
            if tenant_id:
                self._set_rls_context(tenant_id, is_super_admin)

            # Check quotas (only for non-super-admin users)
            if tenant_id and not is_super_admin:
                try:
                    allowed, quota_info = self.quota_service.check_and_increment_api_quota(
                        tenant_id=tenant_id,
                        endpoint=request.endpoint
                    )

                    # Store quota info in g for potential use by endpoint
                    g.quota_info = quota_info

                    # Log warning if approaching limit
                    if quota_info.get('warning_level'):
                        logger.warning(
                            f"Quota {quota_info['warning_level']} for tenant {tenant_id}",
                            extra={
                                "extra_fields": {
                                    "tenant_id": tenant_id,
                                    "endpoint": request.endpoint,
                                    "quota_info": quota_info
                                }
                            }
                        )

                except QuotaExceededError as e:
                    logger.warning(
                        f"Quota exceeded for tenant {tenant_id}",
                        extra={
                            "extra_fields": {
                                "tenant_id": tenant_id,
                                "endpoint": request.endpoint,
                                "details": e.details
                            }
                        }
                    )

                    return jsonify({
                        "error": "quota_exceeded",
                        "message": e.message,
                        "details": e.details
                    }), 429  # Too Many Requests

            return None

        except Exception as e:
            logger.error(f"Error in tenant middleware: {e}", exc_info=e)
            # Fail open - don't block request due to middleware errors
            return None

    def after_request(self, response):
        """
        Process response after request.

        Adds quota headers to response.

        Args:
            response: Flask response object

        Returns:
            Modified response
        """
        try:
            # Add quota information to response headers
            if hasattr(g, 'quota_info') and g.quota_info:
                quota_info = g.quota_info

                if 'hourly' in quota_info:
                    response.headers['X-RateLimit-Limit-Hour'] = str(quota_info['hourly']['limit'])
                    response.headers['X-RateLimit-Remaining-Hour'] = str(
                        quota_info['hourly']['limit'] - quota_info['hourly']['current']
                    )

                if 'daily' in quota_info:
                    response.headers['X-RateLimit-Limit-Day'] = str(quota_info['daily']['limit'])
                    response.headers['X-RateLimit-Remaining-Day'] = str(
                        quota_info['daily']['limit'] - quota_info['daily']['current']
                    )

                if quota_info.get('warning_level'):
                    response.headers['X-RateLimit-Warning'] = quota_info['warning_level']

            # Add tenant ID header (for debugging)
            if hasattr(g, 'tenant_id') and g.tenant_id:
                response.headers['X-Tenant-ID'] = str(g.tenant_id)

        except Exception as e:
            logger.error(f"Error adding quota headers: {e}", exc_info=e)

        return response

    def teardown_request(self, exception=None):
        """
        Cleanup after request.

        Decrements concurrent counter.

        Args:
            exception: Exception if request failed
        """
        try:
            # Decrement concurrent counter
            if hasattr(g, 'tenant_id') and g.tenant_id:
                self.quota_service.decrement_concurrent(g.tenant_id)

            # Clear RLS context
            if hasattr(g, 'tenant_id'):
                self._clear_rls_context()

        except Exception as e:
            logger.error(f"Error in teardown: {e}", exc_info=e)

    def _set_rls_context(self, tenant_id: int, is_super_admin: bool):
        """
        Set PostgreSQL session variables for Row-Level Security.

        Args:
            tenant_id: Tenant ID
            is_super_admin: Whether user is super-admin
        """
        try:
            # Set tenant_id for RLS policies
            self.db_pool.execute_query(
                "SET LOCAL app.current_tenant_id = %s",
                (tenant_id,),
                fetch=False
            )

            # Set super_admin flag for RLS policies
            self.db_pool.execute_query(
                "SET LOCAL app.is_super_admin = %s",
                ('true' if is_super_admin else 'false',),
                fetch=False
            )

            logger.debug(
                f"Set RLS context: tenant_id={tenant_id}, super_admin={is_super_admin}"
            )

        except Exception as e:
            logger.error(f"Failed to set RLS context: {e}", exc_info=e)

    def _clear_rls_context(self):
        """Clear PostgreSQL session variables."""
        try:
            self.db_pool.execute_query(
                "RESET app.current_tenant_id",
                fetch=False
            )
            self.db_pool.execute_query(
                "RESET app.is_super_admin",
                fetch=False
            )
        except Exception as e:
            logger.error(f"Failed to clear RLS context: {e}", exc_info=e)

    def _is_public_endpoint(self) -> bool:
        """
        Check if current endpoint is public (no auth required).

        Returns:
            True if endpoint is public
        """
        # List of public endpoints (no auth required)
        public_endpoints = [
            'health.health_check',
            'health.readiness',
            'health.liveness',
            'docs.swagger_ui',
            'docs.openapi_spec',
            'auth.login',
            'auth.register',
            'static',
        ]

        # Check if endpoint is public
        if request.endpoint in public_endpoints:
            return True

        # Check if path starts with public prefixes
        public_prefixes = [
            '/health',
            '/docs',
            '/api-docs',
            '/swagger',
            '/static',
        ]

        for prefix in public_prefixes:
            if request.path.startswith(prefix):
                return True

        return False


def require_tenant(allow_super_admin: bool = True):
    """
    Decorator to require tenant context.

    Args:
        allow_super_admin: Whether to allow super-admins (default: True)

    Returns:
        Decorated function

    Example:
        @require_tenant()
        def tenant_endpoint():
            tenant_id = g.tenant_id
            ...

        @require_tenant(allow_super_admin=False)
        def tenant_only_endpoint():
            # Super-admins not allowed
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if tenant context exists
            if not hasattr(g, 'tenant_id') or not g.tenant_id:
                if allow_super_admin and hasattr(g, 'is_super_admin') and g.is_super_admin:
                    # Super-admin without tenant context - allow
                    pass
                else:
                    logger.warning(
                        "Tenant context required but not found",
                        extra={
                            "extra_fields": {
                                "endpoint": request.endpoint,
                                "has_tenant": hasattr(g, 'tenant_id'),
                                "tenant_id": getattr(g, 'tenant_id', None)
                            }
                        }
                    )
                    return jsonify({
                        "error": "tenant_required",
                        "message": "This endpoint requires tenant context"
                    }), 403

            # Check super-admin restriction
            if not allow_super_admin and hasattr(g, 'is_super_admin') and g.is_super_admin:
                return jsonify({
                    "error": "super_admin_not_allowed",
                    "message": "This endpoint is not available for super-admins"
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_super_admin():
    """
    Decorator to require super-admin access.

    Returns:
        Decorated function

    Example:
        @require_super_admin()
        def admin_endpoint():
            # Only super-admins can access
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'is_super_admin') or not g.is_super_admin:
                logger.warning(
                    "Super-admin access required",
                    extra={
                        "extra_fields": {
                            "endpoint": request.endpoint,
                            "user_id": getattr(g, 'user_id', None),
                            "tenant_id": getattr(g, 'tenant_id', None)
                        }
                    }
                )
                return jsonify({
                    "error": "super_admin_required",
                    "message": "This endpoint requires super-admin privileges"
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator

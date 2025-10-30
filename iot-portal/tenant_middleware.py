#!/usr/bin/env python3
"""
Tenant Context Middleware
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 6

Extracts tenant_id from JWT token and enforces tenant isolation.

Features:
- Extracts tenant context from authenticated requests
- Validates tenant exists and is active
- Sets Flask g.tenant_id for request scope
- Provides decorators for tenant-aware endpoints
- Enforces quota limits

Author: INSA Automation Corp
Date: October 28, 2025
"""

from flask import g, request, jsonify, current_app
from functools import wraps
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TenantContextMiddleware:
    """
    Middleware to extract and validate tenant context from JWT token.

    Sets g.tenant_id and g.tenant for all authenticated requests.
    """

    def __init__(self, app, db_config):
        """
        Initialize tenant context middleware.

        Args:
            app: Flask application instance
            db_config: Database configuration dict
        """
        self.app = app
        self.db_config = db_config

        # Endpoints that don't require tenant context
        self.exempt_paths = [
            '/health',
            '/api/v1/auth/login',
            '/api/v1/auth/register',
            '/api/v1/tenants/create',  # Superadmin only
            '/api/v1/docs',
            '/apispec',
            '/flasgger_static'
        ]

        logger.info("TenantContextMiddleware initialized")

    def is_exempt(self, path):
        """
        Check if path is exempt from tenant context requirement.

        Args:
            path: Request path

        Returns:
            True if exempt, False otherwise
        """
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    def extract_tenant_from_token(self, token_payload):
        """
        Extract tenant_id from JWT token payload.

        Args:
            token_payload: Decoded JWT payload

        Returns:
            tenant_id (UUID str) or None
        """
        return token_payload.get('tenant_id')

    def validate_tenant(self, tenant_id):
        """
        Validate tenant exists and is active.

        Args:
            tenant_id: UUID string

        Returns:
            Tenant dict or None
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT id, name, slug, status, tier, enabled_features,
                               max_devices, max_users, max_telemetry_points_per_day,
                               max_retention_days
                        FROM tenants
                        WHERE id = %s
                    """, (tenant_id,))

                    tenant = cursor.fetchone()

                    if not tenant:
                        logger.warning(f"Tenant not found: {tenant_id}")
                        return None

                    if tenant['status'] != 'active':
                        logger.warning(f"Tenant not active: {tenant_id} (status: {tenant['status']})")
                        return None

                    return dict(tenant)
            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Failed to validate tenant: {e}")
            return None

    def __call__(self, environ, start_response):
        """
        WSGI middleware entry point.

        Args:
            environ: WSGI environment
            start_response: WSGI start_response callback

        Returns:
            WSGI response
        """
        with self.app.request_context(environ):
            # Skip tenant context for exempt paths
            if self.is_exempt(request.path):
                return self.app(environ, start_response)

            # Extract tenant_id from JWT token (set by auth middleware)
            if hasattr(g, 'current_user') and g.current_user:
                tenant_id = g.current_user.get('tenant_id')

                if not tenant_id:
                    logger.error("No tenant_id in authenticated user token")
                    response = jsonify({
                        'success': False,
                        'error': 'Missing tenant context in token'
                    })
                    return response(environ, start_response)

                # Validate tenant
                tenant = self.validate_tenant(tenant_id)

                if not tenant:
                    response = jsonify({
                        'success': False,
                        'error': 'Invalid or inactive tenant'
                    })
                    return response(environ, start_response)

                # Set tenant context in Flask g
                g.tenant_id = tenant_id
                g.tenant = tenant

                logger.debug(f"Tenant context set: {tenant['name']} ({tenant_id})")

            return self.app(environ, start_response)


# =============================================================================
# Decorators
# =============================================================================

def require_tenant(f):
    """
    Decorator to ensure tenant context is set.

    Usage:
        @app.route('/api/v1/devices')
        @require_auth
        @require_tenant
        def list_devices():
            tenant_id = g.tenant_id
            # Query devices for this tenant

    Args:
        f: Route function

    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_id') or not g.tenant_id:
            return jsonify({
                'success': False,
                'error': 'Tenant context required'
            }), 403

        return f(*args, **kwargs)

    return decorated_function


def check_tenant_quota(quota_type):
    """
    Decorator to check tenant quotas before allowing operation.

    Args:
        quota_type: Type of quota to check ('devices', 'users', 'telemetry_points')

    Usage:
        @app.route('/api/v1/devices', methods=['POST'])
        @require_auth
        @require_tenant
        @check_tenant_quota('devices')
        def create_device():
            # Create device if quota not exceeded

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant') or not g.tenant:
                return jsonify({
                    'success': False,
                    'error': 'Tenant context required'
                }), 403

            tenant = g.tenant

            # Check quota based on type
            try:
                conn = psycopg2.connect(**current_app.config['DB_CONFIG'])
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        if quota_type == 'devices':
                            max_quota = tenant.get('max_devices')
                            if max_quota is not None:
                                cursor.execute(
                                    "SELECT COUNT(*) as count FROM devices WHERE tenant_id = %s",
                                    (g.tenant_id,)
                                )
                                current_count = cursor.fetchone()['count']

                                if current_count >= max_quota:
                                    return jsonify({
                                        'success': False,
                                        'error': f'Device quota exceeded ({current_count}/{max_quota})',
                                        'quota_type': 'devices',
                                        'current': current_count,
                                        'max': max_quota
                                    }), 429  # HTTP 429 Too Many Requests

                        elif quota_type == 'users':
                            max_quota = tenant.get('max_users')
                            if max_quota is not None:
                                cursor.execute(
                                    "SELECT COUNT(*) as count FROM tenant_users WHERE tenant_id = %s",
                                    (g.tenant_id,)
                                )
                                current_count = cursor.fetchone()['count']

                                if current_count >= max_quota:
                                    return jsonify({
                                        'success': False,
                                        'error': f'User quota exceeded ({current_count}/{max_quota})',
                                        'quota_type': 'users',
                                        'current': current_count,
                                        'max': max_quota
                                    }), 429

                        elif quota_type == 'telemetry_points':
                            max_quota = tenant.get('max_telemetry_points_per_day')
                            if max_quota is not None:
                                cursor.execute("""
                                    SELECT COUNT(*) as count FROM telemetry
                                    WHERE tenant_id = %s
                                    AND timestamp >= CURRENT_DATE
                                """, (g.tenant_id,))
                                current_count = cursor.fetchone()['count']

                                if current_count >= max_quota:
                                    return jsonify({
                                        'success': False,
                                        'error': f'Daily telemetry quota exceeded ({current_count}/{max_quota})',
                                        'quota_type': 'telemetry_points',
                                        'current': current_count,
                                        'max': max_quota
                                    }), 429

                finally:
                    conn.close()

            except Exception as e:
                logger.error(f"Failed to check quota: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to validate quota'
                }), 500

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_tenant_admin(f):
    """
    Decorator to ensure user is a tenant admin.

    Usage:
        @app.route('/api/v1/tenants/<tenant_id>/settings', methods=['PATCH'])
        @require_auth
        @require_tenant
        @require_tenant_admin
        def update_tenant_settings(tenant_id):
            # Only tenant admins can modify settings

    Args:
        f: Route function

    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_id') or not hasattr(g, 'current_user'):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401

        # Check if user is tenant admin
        try:
            conn = psycopg2.connect(**current_app.config['DB_CONFIG'])
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT is_tenant_admin FROM tenant_users
                        WHERE tenant_id = %s AND user_id = %s
                    """, (g.tenant_id, g.current_user['id']))

                    result = cursor.fetchone()

                    if not result or not result['is_tenant_admin']:
                        return jsonify({
                            'success': False,
                            'error': 'Tenant admin privileges required'
                        }), 403

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Failed to check tenant admin status: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to verify permissions'
            }), 500

        return f(*args, **kwargs)

    return decorated_function


def check_tenant_feature(feature_name):
    """
    Decorator to check if tenant has a specific feature enabled.

    Args:
        feature_name: Name of feature to check (e.g., 'ml', 'advanced_analytics')

    Usage:
        @app.route('/api/v1/ml/models', methods=['POST'])
        @require_auth
        @require_tenant
        @check_tenant_feature('ml')
        def create_ml_model():
            # Only tenants with ML feature enabled can access

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant') or not g.tenant:
                return jsonify({
                    'success': False,
                    'error': 'Tenant context required'
                }), 403

            enabled_features = g.tenant.get('enabled_features', {})

            if not enabled_features.get(feature_name, False):
                return jsonify({
                    'success': False,
                    'error': f'Feature not enabled for tenant: {feature_name}',
                    'feature': feature_name,
                    'tier': g.tenant.get('tier')
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# =============================================================================
# Helper functions
# =============================================================================

def get_current_tenant():
    """
    Get current tenant from Flask g context.

    Returns:
        Tenant dict or None
    """
    return g.get('tenant')


def get_current_tenant_id():
    """
    Get current tenant ID from Flask g context.

    Returns:
        Tenant ID (UUID str) or None
    """
    return g.get('tenant_id')


def set_tenant_context(tenant_id):
    """
    Manually set tenant context (for testing or background tasks).

    Args:
        tenant_id: UUID string

    Returns:
        True if successful, False otherwise
    """
    try:
        from flask import current_app

        middleware = TenantContextMiddleware(current_app, current_app.config['DB_CONFIG'])
        tenant = middleware.validate_tenant(tenant_id)

        if tenant:
            g.tenant_id = tenant_id
            g.tenant = tenant
            return True

        return False

    except Exception as e:
        logger.error(f"Failed to set tenant context: {e}")
        return False


# =============================================================================
# Example usage
# =============================================================================

if __name__ == '__main__':
    print("=== Tenant Middleware ===\n")
    print("This module provides Flask middleware for multi-tenant isolation.")
    print("\nKey Components:")
    print("  - TenantContextMiddleware: WSGI middleware class")
    print("  - @require_tenant: Decorator to enforce tenant context")
    print("  - @check_tenant_quota: Decorator to enforce quota limits")
    print("  - @require_tenant_admin: Decorator for tenant admin operations")
    print("  - @check_tenant_feature: Decorator to check feature flags")
    print("\nUsage:")
    print("  from tenant_middleware import TenantContextMiddleware, require_tenant")
    print("  ")
    print("  # Initialize middleware")
    print("  app.wsgi_app = TenantContextMiddleware(app.wsgi_app, DB_CONFIG)")
    print("  ")
    print("  # Use decorator on routes")
    print("  @app.route('/api/v1/devices')")
    print("  @require_auth")
    print("  @require_tenant")
    print("  def list_devices():")
    print("      tenant_id = g.tenant_id")
    print("      # Query devices for this tenant")

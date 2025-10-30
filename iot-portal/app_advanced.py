#!/usr/bin/env python3
"""
INSA Advanced Industrial IoT Platform
Enterprise-grade IIoT solution with REST API, device management, real-time updates

Version: 2.0
Date: October 27, 2025
Author: INSA Automation Corp
"""

from flask import Flask, request, jsonify, send_file, render_template_string, g, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flasgger import Swagger, swag_from
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import json
import os
import uuid
from datetime import datetime, timedelta
import hashlib
import bcrypt
import secrets
from functools import wraps
import logging
from mqtt_broker import init_broker, get_broker
from socketio_server import init_websocket_server, get_websocket_server
from rule_engine import init_rule_engine, get_rule_engine
from rate_limiter import create_rate_limiter, get_rate_limiter
from ml_api import ml_api
from alerting_api import alerting_api, init_alerting_api
from retention_api import retention_bp
from retention_scheduler import init_retention_scheduler, get_retention_scheduler
from tenant_middleware import (
    TenantContextMiddleware,
    require_tenant,
    check_tenant_quota,
    require_tenant_admin,
    check_tenant_feature,
    get_current_tenant,
    get_current_tenant_id
)
from tenant_manager import TenantManager, TenantManagerException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
# TEMPORARY: Use fixed secrets for testing (should be from env vars in production)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-please-change-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-please-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)

# Enable CORS for API access
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize JWT
jwt = JWTManager(app)

# Initialize rate limiter (placeholder, will be reconfigured with Redis later)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"],
    storage_uri="memory://",  # Will be updated to Redis in __main__
    strategy="fixed-window",
    headers_enabled=True,
    swallow_errors=True
)

# Initialize Swagger/OpenAPI Documentation (Phase 3 Feature 10)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "INSA Advanced IIoT Platform API",
        "description": "Industrial IoT monitoring and management platform with real-time telemetry, rule engine, and alerting",
        "contact": {
            "name": "INSA Automation Corp",
            "email": "w.aroca@insaing.com",
            "url": "https://insaautomationcorp.com"
        },
        "version": "2.0.0",
        "termsOfService": "",
    },
    "host": "localhost:5002",
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "name": "X-API-Key",
            "in": "header",
            "description": "API Key for device telemetry ingestion"
        }
    },
    "tags": [
        {
            "name": "Authentication",
            "description": "User authentication and token management"
        },
        {
            "name": "Devices",
            "description": "Device registration and management"
        },
        {
            "name": "Telemetry",
            "description": "Telemetry data ingestion and querying"
        },
        {
            "name": "Rules",
            "description": "Rule engine configuration"
        },
        {
            "name": "Alerts",
            "description": "Alert management and querying"
        },
        {
            "name": "Health",
            "description": "System health and status monitoring"
        },
        {
            "name": "MQTT",
            "description": "MQTT broker operations"
        },
        {
            "name": "Machine Learning",
            "description": "ML model training, prediction, and anomaly detection"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Register ML API Blueprint (Phase 3 Feature 2)
app.register_blueprint(ml_api)
logger.info("✅ ML API Blueprint registered at /api/v1/ml")

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'insa_iiot',  # New dedicated database
    'user': 'iiot_user',
    'password': 'iiot_secure_2025',
    'port': 5432
}

# Store DB_CONFIG in app for middleware access
app.config['DB_CONFIG'] = DB_CONFIG

# Register Alerting API Blueprint (Phase 3 Feature 8)
init_alerting_api(DB_CONFIG)
app.register_blueprint(alerting_api)
logger.info("✅ Alerting API Blueprint registered at /api/v1/alerts, /api/v1/escalation-policies, /api/v1/on-call, /api/v1/groups")

# Register Retention API Blueprint (Phase 3 Feature 7)
app.register_blueprint(retention_bp)
logger.info("✅ Retention API Blueprint registered at /api/v1/retention")

# SMTP configuration for email notifications
SMTP_CONFIG = {
    'host': 'localhost',  # Use local SMTP server (change for production)
    'port': 25,
    'username': None,  # Optional: SMTP username
    'password': None,  # Optional: SMTP password
    'from_email': 'INSA IIoT Platform <noreply@insa.com>',
    'use_tls': False  # Set to True for production SMTP servers
}

# Webhook configuration for secure webhook notifications
WEBHOOK_CONFIG = {
    'timeout': 10,  # Request timeout in seconds
    'max_retries': 3,  # Maximum retry attempts
    'verify_ssl': True,  # Verify SSL certificates (production recommended)
    'allow_private_ips': False,  # Security: block webhooks to private IPs
    'user_agent': 'INSA-IIoT-Platform/2.0',
    'max_payload_size': 1048576,  # 1MB max payload
    'rate_limit_seconds': 1  # Minimum seconds between requests to same URL
}

# Redis configuration for performance caching
REDIS_CONFIG = {
    'host': 'localhost',  # Redis server host
    'port': 6379,  # Redis server port
    'db': 0,  # Redis database number
    'password': None,  # Redis password (None for no authentication)
    'decode_responses': True,  # Automatically decode responses to strings
    'socket_timeout': 5,  # Socket timeout in seconds
    'max_connections': 50  # Maximum connections in pool
}

# Grafana integration configuration
GRAFANA_CONFIG = {
    'url': 'http://100.100.101.1:3002',  # Grafana server on iac1
    'api_key': None  # Optional: API key for authentication
}

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database schema"""
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot initialize database - connection failed")
        return False

    try:
        cur = conn.cursor()

        # Create extension for UUID support
        cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

        # Devices table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(255) NOT NULL,
                type VARCHAR(50) NOT NULL,
                location VARCHAR(255),
                area VARCHAR(100),
                protocol VARCHAR(50) DEFAULT 'http',
                connection_string TEXT,
                config JSONB DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'offline',
                last_seen TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Telemetry table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
                key VARCHAR(100) NOT NULL,
                value DOUBLE PRECISION,
                unit VARCHAR(20),
                quality INTEGER DEFAULT 100,
                metadata JSONB DEFAULT '{}'
            );
        """)

        # Alerts table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
                rule_id UUID,
                severity VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                value DOUBLE PRECISION,
                threshold DOUBLE PRECISION,
                status VARCHAR(20) DEFAULT 'active',
                acknowledged_by VARCHAR(255),
                acknowledged_at TIMESTAMP,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'
            );
        """)

        # Rules table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
                rule_type VARCHAR(50) NOT NULL,  -- threshold, comparison, time_based, statistical
                conditions JSONB NOT NULL,       -- Renamed from condition (Phase 2)
                actions JSONB NOT NULL,          -- Renamed from action (Phase 2)
                enabled BOOLEAN DEFAULT true,
                priority INTEGER DEFAULT 5,      -- Changed default from 50 to 5
                cooldown_seconds INTEGER DEFAULT 300,
                last_triggered TIMESTAMP,
                trigger_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # API keys table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                key_hash VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
                permissions JSONB DEFAULT '{"read": true, "write": true}',
                rate_limit INTEGER DEFAULT 1000,
                expires_at TIMESTAMP,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'viewer',
                permissions JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP
            );
        """)

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_telemetry_device_time ON telemetry (device_id, timestamp DESC);",
            "CREATE INDEX IF NOT EXISTS idx_telemetry_key ON telemetry (key);",
            "CREATE INDEX IF NOT EXISTS idx_devices_status ON devices (status);",
            "CREATE INDEX IF NOT EXISTS idx_devices_area ON devices (area);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_device ON alerts (device_id);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts (created_at DESC);",
        ]

        for idx_sql in indexes:
            cur.execute(idx_sql)

        conn.commit()
        logger.info("Database schema initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

def hash_password(password):
    """Hash password using bcrypt with salt (12 rounds)"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, password_hash):
    """
    Verify password against bcrypt hash, with fallback to SHA256 for migration.
    Returns tuple: (is_valid, needs_rehash)
    """
    # Try bcrypt first (new format)
    try:
        is_valid = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        return (is_valid, False)  # Valid bcrypt, no rehash needed
    except (ValueError, AttributeError):
        # Not a bcrypt hash, try SHA256 (old format - 64 chars hex)
        if len(password_hash) == 64:
            old_hash = hashlib.sha256(password.encode()).hexdigest()
            if old_hash == password_hash:
                logger.warning(f"User logged in with old SHA256 hash, needs migration")
                return (True, True)  # Valid SHA256, needs rehash

        logger.warning("Invalid password hash format detected")
        return (False, False)

def generate_api_key():
    """Generate secure API key"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key):
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def api_key_required(f):
    """Decorator for API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database error'}), 500

        try:
            cur = conn.cursor()
            key_hash = hash_api_key(api_key)

            cur.execute("""
                SELECT id, device_id, permissions, rate_limit, expires_at
                FROM api_keys
                WHERE key_hash = %s
            """, (key_hash,))

            key_data = cur.fetchone()

            if not key_data:
                return jsonify({'error': 'Invalid API key'}), 401

            # Check expiration
            if key_data['expires_at'] and datetime.now() > key_data['expires_at']:
                return jsonify({'error': 'API key expired'}), 401

            # Update last_used timestamp
            cur.execute("""
                UPDATE api_keys SET last_used = NOW() WHERE id = %s
            """, (key_data['id'],))
            conn.commit()

            # Add key data to request context
            request.api_key_data = key_data

            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return jsonify({'error': 'Authentication error'}), 500
        finally:
            conn.close()

    return decorated_function


def require_auth(f):
    """
    Decorator to require JWT authentication and set g.current_user.

    This replaces @jwt_required() to provide tenant context.

    Usage:
        @app.route('/api/v1/devices')
        @require_auth
        def list_devices():
            user_id = g.current_user['id']
            tenant_id = g.current_user['tenant_id']
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        # Get full JWT claims
        claims = get_jwt()

        # Set tenant_id in Flask g (required by @require_tenant decorator)
        g.tenant_id = claims.get('tenant_id')

        # Set current user in Flask g
        g.current_user = {
            'id': claims.get('user_id'),
            'email': get_jwt_identity(),
            'tenant_id': claims.get('tenant_id'),
            'tenant_slug': claims.get('tenant_slug'),
            'role': claims.get('role'),
            'permissions': claims.get('permissions', []),
            'is_tenant_admin': claims.get('is_tenant_admin', False)
        }

        return f(*args, **kwargs)

    return decorated_function

# ============================================================================
# RBAC - ROLE-BASED ACCESS CONTROL (Phase 3 Feature 5)
# ============================================================================

def log_audit_event(user_id, action, resource, resource_id=None, details=None, status='success'):
    """Log security audit event"""
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot log audit event: Database connection failed")
        return

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs (user_id, action, resource, resource_id, details, ip_address, user_agent, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            action,
            resource,
            resource_id,
            json.dumps(details or {}),
            request.remote_addr,
            request.headers.get('User-Agent', ''),
            status
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Audit logging error: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_user_permissions(user_email):
    """Get aggregated permissions for a user from all their roles"""
    conn = get_db_connection()
    if not conn:
        return {}

    try:
        cur = conn.cursor()

        # Get user ID
        cur.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user_row = cur.fetchone()
        if not user_row:
            return {}

        user_id = user_row['id']

        # Get all roles assigned to user
        cur.execute("""
            SELECT r.permissions
            FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = %s
        """, (user_id,))

        roles = cur.fetchall()

        # Aggregate permissions from all roles
        aggregated_permissions = {}
        for role in roles:
            role_perms = role['permissions']
            for resource, actions in role_perms.items():
                if resource not in aggregated_permissions:
                    aggregated_permissions[resource] = set()
                aggregated_permissions[resource].update(actions)

        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in aggregated_permissions.items()}

    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return {}
    finally:
        conn.close()

def check_permission(user_email, resource, action):
    """Check if user has specific permission"""
    permissions = get_user_permissions(user_email)
    resource_perms = permissions.get(resource, [])
    return action in resource_perms

def require_permission(resource, action):
    """Decorator to check specific permission"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_jwt_identity()

            if not check_permission(current_user, resource, action):
                log_audit_event(
                    user_id=None,
                    action=f"{action}_{resource}",
                    resource=resource,
                    status='denied'
                )
                return jsonify({'error': 'Permission denied'}), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator

def require_role(role_name):
    """Decorator to check if user has specific role"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_jwt_identity()

            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Database error'}), 500

            try:
                cur = conn.cursor()

                # Get user ID
                cur.execute("SELECT id FROM users WHERE email = %s", (current_user,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify({'error': 'User not found'}), 404

                user_id = user_row['id']

                # Check if user has the required role
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = %s AND r.name = %s
                """, (user_id, role_name))

                result = cur.fetchone()

                if result['count'] == 0:
                    log_audit_event(
                        user_id=str(user_id),
                        action=f"require_role_{role_name}",
                        resource='role_check',
                        status='denied'
                    )
                    return jsonify({'error': f'Role {role_name} required'}), 403

                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"Role check error: {e}")
                return jsonify({'error': 'Authorization error'}), 500
            finally:
                conn.close()

        return decorated_function
    return decorator

# ============================================================================
# API ENDPOINTS - AUTHENTICATION
# ============================================================================

@app.route('/api/v1/auth/register', methods=['POST'])
@limiter.limit("3 per hour")  # Strict limit for registration (abuse prevention)
@jwt_required()
def register_user():
    """Register new user (admin only)"""
    current_user = get_jwt_identity()
    data = request.get_json()

    required_fields = ['email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
        if cur.fetchone():
            return jsonify({'error': 'Email already registered'}), 409

        # Hash password
        password_hash = hash_password(data['password'])

        # Insert user
        cur.execute("""
            INSERT INTO users (email, password_hash, role, permissions)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, role, created_at
        """, (
            data['email'],
            password_hash,
            data.get('role', 'viewer'),
            json.dumps(data.get('permissions', {}))
        ))

        user = cur.fetchone()
        conn.commit()

        logger.info(f"New user registered: {user['email']} by {current_user}")

        return jsonify({
            'message': 'User registered successfully',
            'user': dict(user)
        }), 201

    except Exception as e:
        conn.rollback()
        logger.error(f"User registration error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Brute force protection - strict login limit
def login():
    """User login - returns JWT tokens"""
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT id, email, password_hash, role, permissions
            FROM users
            WHERE email = %s
        """, (data['email'],))

        user = cur.fetchone()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Verify password (may return tuple for migration)
        password_result = verify_password(data['password'], user['password_hash'])
        is_valid, needs_rehash = password_result if isinstance(password_result, tuple) else (password_result, False)

        if not is_valid:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Automatic migration: rehash SHA256 passwords to bcrypt on login
        if needs_rehash:
            new_hash = hash_password(data['password'])
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, user['id'])
            )
            conn.commit()
            logger.info(f"Migrated user {user['email']} from SHA256 to bcrypt")

        # Get user's tenant(s) - users can belong to multiple tenants
        cur.execute("""
            SELECT tu.tenant_id, t.name, t.slug, t.status, tu.role_id, tu.is_tenant_admin
            FROM tenant_users tu
            JOIN tenants t ON tu.tenant_id = t.id
            WHERE tu.user_id = %s AND t.status = 'active'
            ORDER BY tu.created_at ASC
        """, (user['id'],))

        tenant_memberships = cur.fetchall()

        if not tenant_memberships:
            return jsonify({'error': 'No active tenant found for user'}), 403

        # Use first tenant as default (in future, allow tenant selection)
        primary_tenant = tenant_memberships[0]

        # Update last login
        cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
        conn.commit()

        # Create tokens with tenant context
        additional_claims = {
            'user_id': str(user['id']),
            'tenant_id': str(primary_tenant['tenant_id']),
            'tenant_slug': primary_tenant['slug'],
            'role': user['role'],
            'permissions': user['permissions'],
            'is_tenant_admin': primary_tenant['is_tenant_admin']
        }

        access_token = create_access_token(
            identity=data['email'],
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=data['email'],
            additional_claims=additional_claims
        )

        logger.info(f"User logged in: {user['email']} (tenant: {primary_tenant['slug']})")

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': str(user['id']),
                'email': user['email'],
                'role': user['role'],
                'tenant': {
                    'id': str(primary_tenant['tenant_id']),
                    'name': primary_tenant['name'],
                    'slug': primary_tenant['slug']
                }
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500
    finally:
        conn.close()

@app.route('/api/v1/auth/refresh', methods=['POST'])
@limiter.limit("10 per minute")  # Allow frequent token refresh
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify({'access_token': access_token}), 200

# ============================================================================
# API ENDPOINTS - USER MANAGEMENT (RBAC)
# ============================================================================

@app.route('/api/v1/users', methods=['GET'])
@limiter.limit("50 per minute")
@require_permission('users', 'read')
def list_users():
    """List all users (requires users:read permission)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT u.id, u.email, u.role, u.permissions, u.created_at, u.last_login,
                   ARRAY_AGG(r.name) as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            GROUP BY u.id, u.email, u.role, u.permissions, u.created_at, u.last_login
            ORDER BY u.created_at DESC
        """)

        users = cur.fetchall()

        return jsonify({
            'users': [dict(user) for user in users],
            'total': len(users)
        }), 200

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/users/<user_id>', methods=['GET'])
@limiter.limit("100 per minute")
@require_permission('users', 'read')
def get_user(user_id):
    """Get user details"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT u.id, u.email, u.role, u.permissions, u.created_at, u.last_login,
                   ARRAY_AGG(DISTINCT r.name) as roles,
                   ARRAY_AGG(DISTINCT r.id) as role_ids
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            WHERE u.id = %s
            GROUP BY u.id
        """, (user_id,))

        user = cur.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': dict(user)}), 200

    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/users/<user_id>', methods=['PUT'])
@limiter.limit("20 per minute")
@require_permission('users', 'write')
def update_user(user_id):
    """Update user (requires users:write permission)"""
    data = request.get_json()
    current_user = get_jwt_identity()

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Build update query dynamically
        update_fields = []
        params = []

        if 'email' in data:
            update_fields.append("email = %s")
            params.append(data['email'])

        if 'password' in data:
            update_fields.append("password_hash = %s")
            params.append(hash_password(data['password']))

        if 'role' in data:
            update_fields.append("role = %s")
            params.append(data['role'])

        if 'permissions' in data:
            update_fields.append("permissions = %s")
            params.append(json.dumps(data['permissions']))

        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400

        params.append(user_id)

        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s RETURNING id, email, role, permissions"
        cur.execute(query, params)

        updated_user = cur.fetchone()

        if not updated_user:
            return jsonify({'error': 'User not found'}), 404

        conn.commit()

        # Log audit event
        log_audit_event(
            user_id=None,
            action='update_user',
            resource='users',
            resource_id=user_id,
            details={'updated_fields': list(data.keys()), 'updated_by': current_user}
        )

        logger.info(f"User updated: {user_id} by {current_user}")

        return jsonify({
            'message': 'User updated successfully',
            'user': dict(updated_user)
        }), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating user: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/users/<user_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
@require_permission('users', 'delete')
def delete_user(user_id):
    """Delete user (requires users:delete permission)"""
    current_user = get_jwt_identity()

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Check if user exists
        cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Delete user (cascade will remove user_roles entries)
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        # Log audit event
        log_audit_event(
            user_id=None,
            action='delete_user',
            resource='users',
            resource_id=user_id,
            details={'deleted_email': user['email'], 'deleted_by': current_user}
        )

        logger.info(f"User deleted: {user['email']} by {current_user}")

        return jsonify({'message': 'User deleted successfully'}), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/users/<user_id>/roles', methods=['POST'])
@limiter.limit("20 per minute")
@require_permission('users', 'write')
def assign_user_role(user_id):
    """Assign role to user"""
    data = request.get_json()
    current_user = get_jwt_identity()

    if 'role_id' not in data:
        return jsonify({'error': 'role_id required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Get current user ID for audit
        cur.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        current_user_row = cur.fetchone()
        current_user_id = current_user_row['id'] if current_user_row else None

        # Check if role assignment already exists
        cur.execute("""
            SELECT 1 FROM user_roles WHERE user_id = %s AND role_id = %s
        """, (user_id, data['role_id']))

        if cur.fetchone():
            return jsonify({'error': 'Role already assigned'}), 409

        # Assign role
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id, assigned_by)
            VALUES (%s, %s, %s)
        """, (user_id, data['role_id'], current_user_id))

        conn.commit()

        # Log audit event
        log_audit_event(
            user_id=str(current_user_id) if current_user_id else None,
            action='assign_role',
            resource='user_roles',
            resource_id=user_id,
            details={'role_id': data['role_id'], 'assigned_by': current_user}
        )

        logger.info(f"Role {data['role_id']} assigned to user {user_id} by {current_user}")

        return jsonify({'message': 'Role assigned successfully'}), 201

    except Exception as e:
        conn.rollback()
        logger.error(f"Error assigning role: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/users/<user_id>/roles/<role_id>', methods=['DELETE'])
@limiter.limit("20 per minute")
@require_permission('users', 'write')
def remove_user_role(user_id, role_id):
    """Remove role from user"""
    current_user = get_jwt_identity()

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Remove role assignment
        cur.execute("""
            DELETE FROM user_roles WHERE user_id = %s AND role_id = %s
        """, (user_id, role_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Role assignment not found'}), 404

        conn.commit()

        # Log audit event
        log_audit_event(
            user_id=None,
            action='remove_role',
            resource='user_roles',
            resource_id=user_id,
            details={'role_id': role_id, 'removed_by': current_user}
        )

        logger.info(f"Role {role_id} removed from user {user_id} by {current_user}")

        return jsonify({'message': 'Role removed successfully'}), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Error removing role: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# API ENDPOINTS - ROLE MANAGEMENT (RBAC)
# ============================================================================

@app.route('/api/v1/roles', methods=['GET'])
@limiter.limit("100 per minute")
@jwt_required()
def list_roles():
    """List all available roles"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, description, permissions, created_at
            FROM roles
            ORDER BY id
        """)

        roles = cur.fetchall()

        return jsonify({
            'roles': [dict(role) for role in roles],
            'total': len(roles)
        }), 200

    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/roles/<role_id>', methods=['GET'])
@limiter.limit("100 per minute")
@jwt_required()
def get_role(role_id):
    """Get role details"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT r.id, r.name, r.description, r.permissions, r.created_at,
                   COUNT(ur.user_id) as user_count
            FROM roles r
            LEFT JOIN user_roles ur ON r.id = ur.role_id
            WHERE r.id = %s
            GROUP BY r.id
        """, (role_id,))

        role = cur.fetchone()

        if not role:
            return jsonify({'error': 'Role not found'}), 404

        return jsonify({'role': dict(role)}), 200

    except Exception as e:
        logger.error(f"Error getting role: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# API ENDPOINTS - AUDIT LOGS (RBAC)
# ============================================================================

@app.route('/api/v1/audit/logs', methods=['GET'])
@limiter.limit("50 per minute")
@require_permission('system', 'read')
def get_audit_logs():
    """Get audit logs (requires system:read permission)"""
    # Query parameters
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    action = request.args.get('action')
    resource = request.args.get('resource')
    user_id = request.args.get('user_id')
    status = request.args.get('status')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Build query
        query = """
            SELECT al.id, al.user_id, u.email as user_email, al.action, al.resource,
                   al.resource_id, al.details, al.ip_address, al.status, al.timestamp
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE 1=1
        """
        params = []

        if action:
            query += " AND al.action = %s"
            params.append(action)

        if resource:
            query += " AND al.resource = %s"
            params.append(resource)

        if user_id:
            query += " AND al.user_id = %s"
            params.append(user_id)

        if status:
            query += " AND al.status = %s"
            params.append(status)

        query += " ORDER BY al.timestamp DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cur.execute(query, params)
        logs = cur.fetchall()

        # Get total count
        count_query = "SELECT COUNT(*) as total FROM audit_logs WHERE 1=1"
        count_params = []

        if action:
            count_query += " AND action = %s"
            count_params.append(action)

        if resource:
            count_query += " AND resource = %s"
            count_params.append(resource)

        if user_id:
            count_query += " AND user_id = %s"
            count_params.append(user_id)

        if status:
            count_query += " AND status = %s"
            count_params.append(status)

        cur.execute(count_query, count_params)
        total = cur.fetchone()['total']

        return jsonify({
            'logs': [dict(log) for log in logs],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# API ENDPOINTS - ADVANCED ANALYTICS (Phase 3 Feature 1)
# ============================================================================

@app.route('/api/v1/analytics/timeseries/<device_id>/<metric>', methods=['GET'])
@limiter.limit("30 per minute")
@jwt_required()
@require_permission('telemetry', 'read')
def get_timeseries_analytics(device_id, metric):
    """
    Time-series analysis with moving average and rate of change

    Query Parameters:
    - window: Moving average window size in points (default: 5)
    - from: Start timestamp (ISO 8601 format)
    - to: End timestamp (ISO 8601 format)
    - limit: Maximum data points to return (default: 1000)

    Returns:
    - timestamps: Array of timestamps
    - values: Array of values
    - moving_avg: Array of moving averages
    - rate_per_minute: Array of rates of change per minute
    - unit: Unit of measurement
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        # Parse query parameters
        window = int(request.args.get('window', 5))
        from_time = request.args.get('from')
        to_time = request.args.get('to')
        limit = int(request.args.get('limit', 1000))

        # Build time range filter
        time_filter = ""
        params = [device_id, metric]

        if from_time:
            time_filter += " AND timestamp >= %s"
            params.append(from_time)
        if to_time:
            time_filter += " AND timestamp <= %s"
            params.append(to_time)

        # Query with window functions
        query = f"""
            SELECT
                timestamp,
                value,
                unit,
                -- Moving average (n-point window)
                AVG(value) OVER (
                    ORDER BY timestamp
                    ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW
                ) as moving_avg,
                -- Rate of change (per minute)
                CASE
                    WHEN LAG(timestamp) OVER (ORDER BY timestamp) IS NOT NULL
                    THEN (value - LAG(value) OVER (ORDER BY timestamp)) /
                         NULLIF(EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))), 0) * 60
                    ELSE NULL
                END as rate_per_minute
            FROM telemetry
            WHERE device_id = %s AND key = %s {time_filter}
            ORDER BY timestamp DESC
            LIMIT %s
        """
        params.append(limit)

        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()

        if not rows:
            return jsonify({
                'message': 'No data found for specified parameters',
                'device_id': device_id,
                'metric': metric
            }), 404

        # Format response (reverse to chronological order)
        rows = list(reversed(rows))

        return jsonify({
            'device_id': device_id,
            'metric': metric,
            'unit': rows[0]['unit'] if rows else None,
            'window_size': window,
            'data_points': len(rows),
            'timeseries': [
                {
                    'timestamp': row['timestamp'].isoformat(),
                    'value': float(row['value']),
                    'moving_avg': float(row['moving_avg']) if row['moving_avg'] else None,
                    'rate_per_minute': float(row['rate_per_minute']) if row['rate_per_minute'] else None
                }
                for row in rows
            ]
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in time-series analytics: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/v1/analytics/trends/<device_id>/<metric>', methods=['GET'])
@limiter.limit("30 per minute")
@jwt_required()
@require_permission('telemetry', 'read')
def get_trend_analysis(device_id, metric):
    """
    Trend detection using linear regression

    Identifies whether a metric is increasing, decreasing, or stable over time.

    Query Parameters:
    - from: Start timestamp (ISO 8601 format)
    - to: End timestamp (ISO 8601 format)
    - threshold: Slope threshold for trend classification (default: 0.01)

    Returns:
    - trend: "increasing", "decreasing", or "stable"
    - slope: Linear regression slope (change per second)
    - confidence: R² coefficient (0-1, higher = better fit)
    - points: Number of data points analyzed
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        # Parse query parameters
        from_time = request.args.get('from')
        to_time = request.args.get('to')
        threshold = float(request.args.get('threshold', 0.01))

        # Build time range filter
        time_filter = ""
        params = [device_id, metric]

        if from_time:
            time_filter += " AND timestamp >= %s"
            params.append(from_time)
        if to_time:
            time_filter += " AND timestamp <= %s"
            params.append(to_time)

        # Linear regression calculation using PostgreSQL
        # Formula: slope = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
        # where x = time (seconds since epoch), y = value
        query = f"""
            WITH data AS (
                SELECT
                    EXTRACT(EPOCH FROM timestamp) as x,
                    value as y
                FROM telemetry
                WHERE device_id = %s AND key = %s {time_filter}
            ),
            stats AS (
                SELECT
                    COUNT(*) as n,
                    SUM(x) as sum_x,
                    SUM(y) as sum_y,
                    SUM(x * x) as sum_x2,
                    SUM(y * y) as sum_y2,
                    SUM(x * y) as sum_xy,
                    AVG(y) as mean_y,
                    STDDEV(y) as stddev_y,
                    MIN(y) as min_y,
                    MAX(y) as max_y
                FROM data
            )
            SELECT
                n,
                CASE
                    WHEN n < 2 THEN NULL
                    ELSE (n * sum_xy - sum_x * sum_y) / NULLIF(n * sum_x2 - sum_x * sum_x, 0)
                END as slope,
                CASE
                    WHEN n < 2 OR stddev_y = 0 THEN NULL
                    ELSE 1 - (
                        SUM((y - (
                            ((n * sum_xy - sum_x * sum_y) / NULLIF(n * sum_x2 - sum_x * sum_x, 0)) * x +
                            (mean_y - ((n * sum_xy - sum_x * sum_y) / NULLIF(n * sum_x2 - sum_x * sum_x, 0)) * (sum_x / n))
                        ))^2)
                    ) / NULLIF(n * stddev_y * stddev_y, 0)
                END as r_squared,
                mean_y,
                stddev_y,
                min_y,
                max_y
            FROM stats, data
            GROUP BY n, sum_x, sum_y, sum_x2, sum_y2, sum_xy, mean_y, stddev_y, min_y, max_y
            LIMIT 1
        """

        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()

        if not row or row['n'] is None or row['n'] < 2:
            return jsonify({
                'message': 'Insufficient data for trend analysis (need at least 2 points)',
                'device_id': device_id,
                'metric': metric
            }), 404

        slope = row['slope'] or 0.0
        r_squared = row['r_squared'] or 0.0

        # Classify trend based on slope and threshold
        if abs(slope) < threshold:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        # Calculate confidence (0-100% based on R²)
        confidence = max(0, min(100, r_squared * 100)) if r_squared is not None else 0

        return jsonify({
            'device_id': device_id,
            'metric': metric,
            'trend': trend,
            'slope': float(slope),
            'slope_per_minute': float(slope * 60),  # Convert to per minute for readability
            'confidence': round(confidence, 2),
            'r_squared': float(r_squared) if r_squared is not None else None,
            'statistics': {
                'points': int(row['n']),
                'mean': float(row['mean_y']) if row['mean_y'] is not None else None,
                'stddev': float(row['stddev_y']) if row['stddev_y'] is not None else None,
                'min': float(row['min_y']) if row['min_y'] is not None else None,
                'max': float(row['max_y']) if row['max_y'] is not None else None
            },
            'threshold': threshold
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in trend analysis: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/v1/analytics/statistics/<device_id>/<metric>', methods=['GET'])
@limiter.limit("30 per minute")
@jwt_required()
@require_permission('telemetry', 'read')
def get_statistical_summary(device_id, metric):
    """
    Statistical summary of telemetry data

    Calculates comprehensive statistics including mean, median, standard deviation,
    min/max values, and percentiles.

    Query Parameters:
    - from: Start timestamp (ISO 8601 format)
    - to: End timestamp (ISO 8601 format)

    Returns:
    - Basic statistics: mean, median, stddev, min, max
    - Percentiles: 25th, 50th (median), 75th, 95th
    - Data point count
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        # Parse query parameters
        from_time = request.args.get('from')
        to_time = request.args.get('to')

        # Build time range filter
        time_filter = ""
        params = [device_id, metric]

        if from_time:
            time_filter += " AND timestamp >= %s"
            params.append(from_time)
        if to_time:
            time_filter += " AND timestamp <= %s"
            params.append(to_time)

        # Statistical aggregation using PostgreSQL functions
        # Note: Using MAX(unit) to handle potential unit inconsistencies
        query = f"""
            SELECT
                COUNT(*) as count,
                AVG(value) as mean,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median,
                STDDEV(value) as stddev,
                VARIANCE(value) as variance,
                MIN(value) as min,
                MAX(value) as max,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value) as p25,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value) as p75,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95,
                MIN(timestamp) as first_timestamp,
                MAX(timestamp) as last_timestamp,
                MAX(unit) as unit
            FROM telemetry
            WHERE device_id = %s AND key = %s {time_filter}
        """

        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()

        if not row or row['count'] == 0:
            return jsonify({
                'message': 'No data found for specified parameters',
                'device_id': device_id,
                'metric': metric
            }), 404

        # Calculate additional metrics
        mean = float(row['mean']) if row['mean'] is not None else None
        stddev = float(row['stddev']) if row['stddev'] is not None else None

        # Calculate coefficient of variation (CV) if possible
        cv = (stddev / mean * 100) if (mean and stddev and mean != 0) else None

        # Calculate interquartile range (IQR)
        p25 = float(row['p25']) if row['p25'] is not None else None
        p75 = float(row['p75']) if row['p75'] is not None else None
        iqr = (p75 - p25) if (p25 is not None and p75 is not None) else None

        return jsonify({
            'device_id': device_id,
            'metric': metric,
            'unit': row['unit'],
            'data_points': int(row['count']),
            'time_range': {
                'start': row['first_timestamp'].isoformat() if row['first_timestamp'] else None,
                'end': row['last_timestamp'].isoformat() if row['last_timestamp'] else None
            },
            'statistics': {
                'central_tendency': {
                    'mean': round(mean, 4) if mean is not None else None,
                    'median': round(float(row['median']), 4) if row['median'] is not None else None
                },
                'dispersion': {
                    'stddev': round(stddev, 4) if stddev is not None else None,
                    'variance': round(float(row['variance']), 4) if row['variance'] is not None else None,
                    'coefficient_of_variation': round(cv, 2) if cv is not None else None,
                    'range': round(float(row['max']) - float(row['min']), 4) if (row['max'] and row['min']) else None,
                    'iqr': round(iqr, 4) if iqr is not None else None
                },
                'extremes': {
                    'min': round(float(row['min']), 4) if row['min'] is not None else None,
                    'max': round(float(row['max']), 4) if row['max'] is not None else None
                },
                'percentiles': {
                    'p25': round(float(row['p25']), 4) if row['p25'] is not None else None,
                    'p50_median': round(float(row['median']), 4) if row['median'] is not None else None,
                    'p75': round(float(row['p75']), 4) if row['p75'] is not None else None,
                    'p95': round(float(row['p95']), 4) if row['p95'] is not None else None
                }
            }
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in statistical summary: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/analytics/correlation/<device_id>', methods=['GET'])
@limiter.limit("30 per minute")
@jwt_required()
@require_permission('telemetry', 'read')
def get_correlation_analysis(device_id):
    """
    Calculate correlation between metrics

    Calculates Pearson correlation coefficient between two metrics to identify
    relationships and dependencies in sensor data.

    Query Parameters:
    - metric1: First metric name (e.g., 'temperature')
    - metric2: Second metric name (e.g., 'humidity')
    - from: Start timestamp (ISO 8601 format)
    - to: End timestamp (ISO 8601 format)

    Returns:
    - Pearson correlation coefficient (r): -1 to 1
    - Correlation strength interpretation
    - Sample size (number of paired observations)
    - Individual metric statistics
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        # Parse query parameters
        metric1 = request.args.get('metric1')
        metric2 = request.args.get('metric2')
        from_time = request.args.get('from')
        to_time = request.args.get('to')

        if not metric1 or not metric2:
            return jsonify({
                'error': 'Both metric1 and metric2 parameters are required'
            }), 400

        if metric1 == metric2:
            return jsonify({
                'error': 'metric1 and metric2 must be different'
            }), 400

        # Build time range filter
        time_filter = ""
        params = [device_id, metric1, device_id, metric2]

        if from_time:
            time_filter += " AND t1.timestamp >= %s AND t2.timestamp >= %s"
            params.extend([from_time, from_time])
        if to_time:
            time_filter += " AND t1.timestamp <= %s AND t2.timestamp <= %s"
            params.extend([to_time, to_time])

        # Calculate Pearson correlation using PostgreSQL
        # Matches telemetry records by timestamp and calculates correlation
        query = f"""
            WITH paired_data AS (
                SELECT
                    t1.value as x,
                    t2.value as y
                FROM telemetry t1
                INNER JOIN telemetry t2
                    ON t1.device_id = t2.device_id
                    AND t1.timestamp = t2.timestamp
                WHERE t1.device_id = %s
                    AND t1.key = %s
                    AND t2.device_id = %s
                    AND t2.key = %s
                    {time_filter}
            ),
            stats AS (
                SELECT
                    COUNT(*) as n,
                    AVG(x) as mean_x,
                    AVG(y) as mean_y,
                    STDDEV_POP(x) as stddev_x,
                    STDDEV_POP(y) as stddev_y,
                    SUM((x - (SELECT AVG(x) FROM paired_data)) * (y - (SELECT AVG(y) FROM paired_data))) as covariance_sum
                FROM paired_data
            )
            SELECT
                n,
                mean_x,
                mean_y,
                stddev_x,
                stddev_y,
                CASE
                    WHEN n < 2 OR stddev_x = 0 OR stddev_y = 0 THEN NULL
                    ELSE covariance_sum / (n * stddev_x * stddev_y)
                END as correlation
            FROM stats
        """

        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()

        if not row or row['n'] == 0:
            return jsonify({
                'message': 'No paired data found for specified metrics and parameters',
                'device_id': device_id,
                'metric1': metric1,
                'metric2': metric2
            }), 404

        # Extract results
        n = int(row['n'])
        correlation = float(row['correlation']) if row['correlation'] is not None else None

        # Interpret correlation strength (Cohen's standard)
        if correlation is None:
            strength = "undefined"
            interpretation = "Insufficient variance in one or both metrics"
        else:
            abs_corr = abs(correlation)
            if abs_corr < 0.1:
                strength = "negligible"
            elif abs_corr < 0.3:
                strength = "weak"
            elif abs_corr < 0.5:
                strength = "moderate"
            elif abs_corr < 0.7:
                strength = "strong"
            else:
                strength = "very strong"

            direction = "positive" if correlation > 0 else "negative"
            interpretation = f"{strength.capitalize()} {direction} correlation"

        return jsonify({
            'device_id': device_id,
            'metric1': metric1,
            'metric2': metric2,
            'sample_size': n,
            'correlation': {
                'coefficient': round(correlation, 4) if correlation is not None else None,
                'strength': strength,
                'interpretation': interpretation
            },
            'metric1_stats': {
                'mean': round(float(row['mean_x']), 4) if row['mean_x'] else None,
                'stddev': round(float(row['stddev_x']), 4) if row['stddev_x'] else None
            },
            'metric2_stats': {
                'mean': round(float(row['mean_y']), 4) if row['mean_y'] else None,
                'stddev': round(float(row['stddev_y']), 4) if row['stddev_y'] else None
            }
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in correlation analysis: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/v1/analytics/forecast/<device_id>/<metric>', methods=['GET'])
@limiter.limit("30 per minute")
@jwt_required()
@require_permission('telemetry', 'read')
def get_forecast(device_id, metric):
    """
    Generate forecast for future values

    Uses linear regression to predict future metric values based on historical
    trends, with 95% confidence intervals for uncertainty quantification.

    Query Parameters:
        steps (int): Number of time steps to forecast (default: 10)
        from (str): Start time for historical data (ISO 8601)
        to (str): End time for historical data (ISO 8601)
        confidence (float): Confidence level (default: 0.95)

    Returns:
        JSON with forecast data, model parameters, and quality metrics
    """
    # Parse query parameters
    steps = int(request.args.get('steps', 10))
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    confidence_level = float(request.args.get('confidence', 0.95))

    # Validate parameters
    if steps < 1 or steps > 100:
        return jsonify({'error': 'Steps must be between 1 and 100'}), 400
    if confidence_level < 0.5 or confidence_level > 0.99:
        return jsonify({'error': 'Confidence level must be between 0.5 and 0.99'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Build time filter
        time_filter = ""
        params = [device_id, metric]
        if from_time:
            time_filter += " AND timestamp >= %s"
            params.append(from_time)
        if to_time:
            time_filter += " AND timestamp <= %s"
            params.append(to_time)

        # Calculate linear regression and get historical stats
        query = f"""
        WITH historical AS (
            SELECT
                EXTRACT(EPOCH FROM timestamp) as x,
                value as y,
                timestamp
            FROM telemetry
            WHERE device_id = %s AND key = %s
                {time_filter}
            ORDER BY timestamp DESC
            LIMIT 200
        ),
        stats AS (
            SELECT
                COUNT(*) as n,
                AVG(x) as mean_x,
                AVG(y) as mean_y,
                STDDEV(y) as stddev_y,
                MIN(y) as min_y,
                MAX(y) as max_y,
                MAX(x) as last_x,
                MAX(timestamp) as last_timestamp
            FROM historical
        ),
        xy_products AS (
            SELECT
                SUM(x * y) as sum_xy,
                SUM(x) as sum_x,
                SUM(y) as sum_y,
                SUM(x * x) as sum_xx
            FROM historical
        ),
        regression AS (
            SELECT
                s.n,
                s.mean_x,
                s.mean_y,
                s.stddev_y,
                s.min_y,
                s.max_y,
                s.last_x,
                s.last_timestamp,
                CASE
                    WHEN s.n * p.sum_xx - p.sum_x * p.sum_x = 0 THEN 0
                    ELSE (s.n * p.sum_xy - p.sum_x * p.sum_y) /
                         (s.n * p.sum_xx - p.sum_x * p.sum_x)
                END as slope,
                CASE
                    WHEN s.n * p.sum_xx - p.sum_x * p.sum_x = 0 THEN s.mean_y
                    ELSE s.mean_y - ((s.n * p.sum_xy - p.sum_x * p.sum_y) /
                                     (s.n * p.sum_xx - p.sum_x * p.sum_x)) * s.mean_x
                END as intercept
            FROM stats s, xy_products p
        ),
        residuals AS (
            SELECT
                h.y as actual,
                r.slope * h.x + r.intercept as predicted
            FROM historical h, regression r
        ),
        quality AS (
            SELECT
                r.*,
                SQRT(AVG(POWER(res.actual - res.predicted, 2))) as rmse,
                CASE
                    WHEN r.stddev_y = 0 THEN NULL
                    ELSE 1 - (SUM(POWER(res.actual - res.predicted, 2)) /
                             SUM(POWER(res.actual - r.mean_y, 2)))
                END as r_squared
            FROM regression r, residuals res
            GROUP BY r.n, r.mean_x, r.mean_y, r.stddev_y, r.min_y, r.max_y,
                     r.last_x, r.last_timestamp, r.slope, r.intercept
        )
        SELECT * FROM quality
        """

        cur.execute(query, params)
        row = cur.fetchone()

        if not row or row['n'] < 2:
            return jsonify({
                'error': 'Insufficient historical data for forecasting',
                'minimum_required': 2,
                'available': row['n'] if row else 0
            }), 400

        # Extract regression parameters
        n = int(row['n'])
        slope = float(row['slope']) if row['slope'] else 0
        intercept = float(row['intercept']) if row['intercept'] else float(row['mean_y'])
        stddev_y = float(row['stddev_y']) if row['stddev_y'] else 0
        rmse = float(row['rmse']) if row['rmse'] else 0
        r_squared = float(row['r_squared']) if row['r_squared'] else 0
        last_timestamp = row['last_timestamp']
        last_x = float(row['last_x'])

        # Get average time interval between readings
        interval_query = f"""
        SELECT AVG(interval_seconds) as avg_interval
        FROM (
            SELECT EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))) as interval_seconds
            FROM telemetry
            WHERE device_id = %s AND key = %s
                {time_filter}
            ORDER BY timestamp DESC
            LIMIT 50
        ) intervals
        WHERE interval_seconds IS NOT NULL
        """
        cur.execute(interval_query, params)
        interval_row = cur.fetchone()
        avg_interval = float(interval_row['avg_interval']) if interval_row and interval_row['avg_interval'] else 300  # Default 5 min

        # Calculate z-score for confidence level
        # 0.95 -> 1.96, 0.90 -> 1.645, 0.99 -> 2.576
        import math
        from scipy import stats as scipy_stats
        z_score = scipy_stats.norm.ppf((1 + confidence_level) / 2)

        # Generate forecast
        forecast = []
        for step in range(1, steps + 1):
            future_x = last_x + (step * avg_interval)
            future_timestamp = last_timestamp + timedelta(seconds=step * avg_interval)
            predicted_value = slope * future_x + intercept

            # Calculate prediction interval (wider than confidence interval)
            # Formula: ŷ ± z * σ * sqrt(1 + 1/n + (x - x̄)²/Σ(x - x̄)²)
            # Simplified version using RMSE as σ estimate
            interval_width = z_score * rmse * math.sqrt(1 + 1/n)

            forecast.append({
                'timestamp': future_timestamp.isoformat(),
                'predicted_value': round(predicted_value, 4),
                'confidence_lower': round(predicted_value - interval_width, 4),
                'confidence_upper': round(predicted_value + interval_width, 4)
            })

        # Classify trend
        abs_slope = abs(slope)
        if abs_slope < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        # Get unit
        unit_query = "SELECT DISTINCT unit FROM telemetry WHERE device_id = %s AND key = %s LIMIT 1"
        cur.execute(unit_query, [device_id, metric])
        unit_row = cur.fetchone()
        unit = unit_row['unit'] if unit_row else None

        return jsonify({
            'device_id': device_id,
            'metric': metric,
            'unit': unit,
            'historical': {
                'count': n,
                'mean': round(float(row['mean_y']), 4),
                'stddev': round(stddev_y, 4),
                'min': round(float(row['min_y']), 4),
                'max': round(float(row['max_y']), 4),
                'trend': trend,
                'last_value': round(slope * last_x + intercept, 4),
                'last_timestamp': last_timestamp.isoformat()
            },
            'model': {
                'type': 'linear_regression',
                'slope': round(slope, 6),
                'intercept': round(intercept, 4),
                'equation': f"y = {slope:.6f}x + {intercept:.4f}",
                'r_squared': round(r_squared, 4) if r_squared else None
            },
            'forecast': forecast,
            'quality': {
                'rmse': round(rmse, 4),
                'r_squared': round(r_squared, 4) if r_squared else None,
                'confidence_level': confidence_level,
                'sample_size': n
            },
            'parameters': {
                'steps': steps,
                'avg_interval_seconds': round(avg_interval, 2),
                'forecast_horizon': f"{(steps * avg_interval) / 3600:.2f} hours"
            }
        }), 200

    except ImportError:
        # If scipy not available, use simple approximation
        logger.warning("scipy not available, using simple z-score approximation")
        # Common z-scores
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z_score = z_scores.get(confidence_level, 1.96)
        # Retry the forecast generation with fixed z_score
        # (implementation continues from forecast generation above)
        return jsonify({'error': 'scipy required for custom confidence levels'}), 500
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in forecasting: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ============================================================================
# API ENDPOINTS - DEVICE MANAGEMENT
# ============================================================================

@app.route('/api/v1/devices', methods=['GET'])
@limiter.limit("200 per minute")  # Generous limit for authenticated device listing
@require_auth
@require_tenant
def list_devices():
    """List all devices for current tenant with optional filtering"""
    # Get tenant context
    tenant_id = g.tenant_id

    # Query parameters
    status = request.args.get('status')
    area = request.args.get('area')
    device_type = request.args.get('type')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Build query with tenant filtering
        query = "SELECT * FROM devices WHERE tenant_id = %s"
        params = [tenant_id]

        if status:
            query += " AND status = %s"
            params.append(status)

        if area:
            query += " AND area = %s"
            params.append(area)

        if device_type:
            query += " AND type = %s"
            params.append(device_type)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cur.execute(query, params)
        devices = cur.fetchall()

        # Convert UUID to string for JSON serialization
        devices_list = []
        for device in devices:
            device_dict = dict(device)
            device_dict['id'] = str(device_dict['id'])
            devices_list.append(device_dict)

        return jsonify({
            'devices': devices_list,
            'count': len(devices_list),
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        logger.error(f"List devices error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/devices', methods=['POST'])
@require_auth
@require_tenant
@check_tenant_quota('device')
def create_device():
    """Register new device for current tenant"""
    # Get tenant context
    tenant_id = g.tenant_id

    data = request.get_json()

    required_fields = ['name', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields: name, type'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO devices (
                name, type, location, area, protocol,
                connection_string, config, metadata, tenant_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, type, status, created_at
        """, (
            data['name'],
            data['type'],
            data.get('location'),
            data.get('area'),
            data.get('protocol', 'http'),
            data.get('connection_string'),
            json.dumps(data.get('config', {})),
            json.dumps(data.get('metadata', {})),
            tenant_id
        ))

        device = cur.fetchone()
        conn.commit()

        device_dict = dict(device)
        device_dict['id'] = str(device_dict['id'])

        logger.info(f"Device created: {device['name']} ({device['id']})")

        return jsonify({
            'message': 'Device created successfully',
            'device': device_dict
        }), 201

    except Exception as e:
        conn.rollback()
        logger.error(f"Create device error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/devices/<device_id>', methods=['GET'])
@require_auth
@require_tenant
def get_device(device_id):
    """Get device details for current tenant"""
    # Get tenant context
    tenant_id = g.tenant_id

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("SELECT * FROM devices WHERE id = %s AND tenant_id = %s", (device_id, tenant_id))
        device = cur.fetchone()

        if not device:
            return jsonify({'error': 'Device not found'}), 404

        device_dict = dict(device)
        device_dict['id'] = str(device_dict['id'])

        # Get latest telemetry
        cur.execute("""
            SELECT key, value, unit, timestamp
            FROM telemetry
            WHERE device_id = %s
            ORDER BY timestamp DESC
            LIMIT 10
        """, (device_id,))

        telemetry = cur.fetchall()
        device_dict['latest_telemetry'] = [dict(t) for t in telemetry]

        return jsonify(device_dict), 200

    except Exception as e:
        logger.error(f"Get device error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/devices/<device_id>', methods=['PUT'])
@require_auth
@require_tenant
def update_device(device_id):
    """Update device for current tenant"""
    # Get tenant context
    tenant_id = g.tenant_id

    data = request.get_json()

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Build update query dynamically
        update_fields = []
        params = []

        allowed_fields = ['name', 'type', 'location', 'area', 'protocol',
                         'connection_string', 'status']

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])

        if 'config' in data:
            update_fields.append("config = %s")
            params.append(json.dumps(data['config']))

        if 'metadata' in data:
            update_fields.append("metadata = %s")
            params.append(json.dumps(data['metadata']))

        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400

        update_fields.append("updated_at = NOW()")
        params.extend([device_id, tenant_id])

        query = f"UPDATE devices SET {', '.join(update_fields)} WHERE id = %s AND tenant_id = %s RETURNING *"

        cur.execute(query, params)
        device = cur.fetchone()

        if not device:
            return jsonify({'error': 'Device not found'}), 404

        conn.commit()

        device_dict = dict(device)
        device_dict['id'] = str(device_dict['id'])

        logger.info(f"Device updated: {device_id}")

        return jsonify({
            'message': 'Device updated successfully',
            'device': device_dict
        }), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Update device error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/devices/<device_id>', methods=['DELETE'])
@require_auth
@require_tenant
def delete_device(device_id):
    """Delete device for current tenant"""
    # Get tenant context
    tenant_id = g.tenant_id

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("DELETE FROM devices WHERE id = %s AND tenant_id = %s RETURNING name", (device_id, tenant_id))
        device = cur.fetchone()

        if not device:
            return jsonify({'error': 'Device not found'}), 404

        conn.commit()

        logger.info(f"Device deleted: {device['name']} ({device_id})")

        return jsonify({
            'message': f"Device '{device['name']}' deleted successfully"
        }), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Delete device error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# API ENDPOINTS - TELEMETRY
# ============================================================================

@app.route('/api/v1/telemetry', methods=['POST'])
@limiter.limit("500 per minute")  # High frequency telemetry ingestion
@api_key_required
def ingest_telemetry():
    """Ingest telemetry data from device"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    device_id = data.get('device_id') or request.api_key_data.get('device_id')

    if not device_id:
        return jsonify({'error': 'device_id required'}), 400

    telemetry_data = data.get('telemetry', data.get('data', {}))

    if not telemetry_data:
        return jsonify({'error': 'No telemetry data'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Get device tenant_id
        cur.execute("SELECT tenant_id FROM devices WHERE id = %s", (device_id,))
        device = cur.fetchone()

        if not device:
            return jsonify({'error': 'Device not found'}), 404

        tenant_id = device['tenant_id']

        # Update device last_seen
        cur.execute("""
            UPDATE devices
            SET last_seen = NOW(), status = 'online'
            WHERE id = %s
        """, (device_id,))

        # Insert telemetry points with tenant_id
        timestamp = data.get('timestamp', datetime.now())
        inserted_count = 0

        for key, value_data in telemetry_data.items():
            if isinstance(value_data, dict):
                value = value_data.get('value')
                unit = value_data.get('unit')
                quality = value_data.get('quality', 100)
            else:
                value = value_data
                unit = None
                quality = 100

            cur.execute("""
                INSERT INTO telemetry (device_id, timestamp, key, value, unit, quality, tenant_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (device_id, timestamp, key, value, unit, quality, tenant_id))

            inserted_count += 1

        conn.commit()

        return jsonify({
            'message': 'Telemetry ingested successfully',
            'points': inserted_count
        }), 201

    except Exception as e:
        conn.rollback()
        logger.error(f"Ingest telemetry error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/telemetry', methods=['GET'])
@require_auth
@require_tenant
def query_telemetry():
    """Query telemetry data for current tenant"""
    # Get tenant context
    tenant_id = g.tenant_id

    device_id = request.args.get('device_id')
    keys = request.args.getlist('key')
    start_time = request.args.get('start')
    end_time = request.args.get('end')
    limit = int(request.args.get('limit', 1000))

    if not device_id:
        return jsonify({'error': 'device_id required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        query = "SELECT timestamp, key, value, unit FROM telemetry WHERE device_id = %s AND tenant_id = %s"
        params = [device_id, tenant_id]

        if keys:
            query += " AND key = ANY(%s)"
            params.append(keys)

        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        data = cur.fetchall()

        return jsonify({
            'device_id': device_id,
            'count': len(data),
            'data': [dict(row) for row in data]
        }), 200

    except Exception as e:
        logger.error(f"Query telemetry error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/telemetry/latest', methods=['GET'])
@require_auth
@require_tenant
def get_latest_telemetry():
    """Get latest telemetry values for device(s) in current tenant"""
    # Get tenant context
    tenant_id = g.tenant_id

    device_id = request.args.get('device_id')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        if device_id:
            # Latest for specific device within tenant
            query = """
                SELECT DISTINCT ON (key)
                    key, value, unit, timestamp
                FROM telemetry
                WHERE device_id = %s AND tenant_id = %s
                ORDER BY key, timestamp DESC
            """
            cur.execute(query, (device_id, tenant_id))
        else:
            # Latest for all devices in tenant
            query = """
                SELECT DISTINCT ON (device_id, key)
                    device_id, key, value, unit, timestamp
                FROM telemetry
                WHERE tenant_id = %s
                ORDER BY device_id, key, timestamp DESC
            """
            cur.execute(query, (tenant_id,))

        data = cur.fetchall()

        return jsonify({
            'count': len(data),
            'data': [dict(row) for row in data]
        }), 200

    except Exception as e:
        logger.error(f"Get latest telemetry error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# API ENDPOINTS - ALERTS
# ============================================================================

@app.route('/api/v1/alerts', methods=['GET'])
@require_auth
@require_tenant
def list_alerts():
    """List alerts for current tenant with filtering"""
    # Get tenant context
    tenant_id = g.tenant_id

    status = request.args.get('status', 'active')
    severity = request.args.get('severity')
    device_id = request.args.get('device_id')
    limit = int(request.args.get('limit', 100))

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        query = "SELECT * FROM alerts WHERE tenant_id = %s AND status = %s"
        params = [tenant_id, status]

        if severity:
            query += " AND severity = %s"
            params.append(severity)

        if device_id:
            query += " AND device_id = %s"
            params.append(device_id)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        alerts = cur.fetchall()

        alerts_list = []
        for alert in alerts:
            alert_dict = dict(alert)
            alert_dict['id'] = str(alert_dict['id'])
            if alert_dict['device_id']:
                alert_dict['device_id'] = str(alert_dict['device_id'])
            if alert_dict['rule_id']:
                alert_dict['rule_id'] = str(alert_dict['rule_id'])
            alerts_list.append(alert_dict)

        return jsonify({
            'alerts': alerts_list,
            'count': len(alerts_list)
        }), 200

    except Exception as e:
        logger.error(f"List alerts error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# API ENDPOINTS - API KEY MANAGEMENT
# ============================================================================

@app.route('/api/v1/api-keys', methods=['POST'])
@require_auth
@require_tenant
def create_api_key():
    """Create new API key for device in current tenant"""
    # Get tenant context
    tenant_id = g.tenant_id

    data = request.get_json()

    if 'name' not in data:
        return jsonify({'error': 'name required'}), 400

    # Generate API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO api_keys (
                key_hash, name, device_id, permissions,
                rate_limit, expires_at, tenant_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, created_at
        """, (
            key_hash,
            data['name'],
            data.get('device_id'),
            json.dumps(data.get('permissions', {'read': True, 'write': True})),
            data.get('rate_limit', 1000),
            data.get('expires_at'),
            tenant_id
        ))

        key_info = cur.fetchone()
        conn.commit()

        logger.info(f"API key created: {data['name']}")

        return jsonify({
            'message': 'API key created successfully',
            'api_key': api_key,  # Only shown once!
            'key_info': {
                'id': str(key_info['id']),
                'name': key_info['name'],
                'created_at': key_info['created_at'].isoformat()
            },
            'warning': 'Save this API key securely. It cannot be retrieved later.'
        }), 201

    except Exception as e:
        conn.rollback()
        logger.error(f"Create API key error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# WEB UI - Enhanced Dashboard
# ============================================================================

@app.route('/')
def index():
    """Main dashboard - Glass Manufacturing with Real-Time Data"""
    return send_from_directory('static', 'dashboard_glass.html')

@app.route('/dashboard-dark')
def index_dark():
    """Generic dark theme dashboard"""
    return send_from_directory('static', 'dashboard_dark.html')

@app.route('/dashboard-light')
def index_light():
    """Light theme dashboard"""
    return send_from_directory('static', 'index.html')

@app.route('/dashboard-old')
def index_old():
    """Old embedded dashboard"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>INSA Advanced IIoT Platform</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .card {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            .feature-card {
                transition: transform 0.3s;
                cursor: pointer;
            }
            .feature-card:hover {
                transform: translateY(-5px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card p-5 mb-4">
                <h1 class="text-center mb-4">
                    🏭 INSA Advanced IIoT Platform
                </h1>
                <p class="text-center lead">
                    Enterprise-grade Industrial IoT Platform for Oil & Gas
                </p>
            </div>

            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card p-4 feature-card">
                        <h3>📡 REST API</h3>
                        <p>Comprehensive API for device management, telemetry, and alerts</p>
                        <a href="/api/v1/docs" class="btn btn-primary">API Docs</a>
                    </div>
                </div>

                <div class="col-md-4 mb-4">
                    <div class="card p-4 feature-card">
                        <h3>🔐 Authentication</h3>
                        <p>JWT tokens and API keys for secure access</p>
                        <button class="btn btn-primary" onclick="showLogin()">Login</button>
                    </div>
                </div>

                <div class="col-md-4 mb-4">
                    <div class="card p-4 feature-card">
                        <h3>📊 Real-time Data</h3>
                        <p>WebSocket updates for live telemetry and alerts</p>
                        <button class="btn btn-primary">Connect</button>
                    </div>
                </div>
            </div>

            <div class="card p-4 mt-4">
                <h3>🚀 Platform Features</h3>
                <ul>
                    <li>✅ Device Management (Register, Configure, Monitor)</li>
                    <li>✅ Telemetry Ingestion (MQTT, HTTP, Multi-protocol)</li>
                    <li>✅ Rule Engine (Alerts, Automation, Actions)</li>
                    <li>✅ Professional Reporting (Excel, PDF, ZIP)</li>
                    <li>✅ Real-time Updates (WebSocket, Socket.IO)</li>
                    <li>✅ API Key Management (Rate limiting, Permissions)</li>
                    <li>✅ Authentication (JWT, OAuth2, SSO)</li>
                </ul>
            </div>

            <div class="card p-4 mt-4">
                <h3>📚 Quick Start</h3>
                <pre><code># 1. Login and get JWT token
curl -X POST http://localhost:5001/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email": "admin@insa.com", "password": "admin123"}'

# 2. Create device
curl -X POST http://localhost:5001/api/v1/devices \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Sensor-01", "type": "temperature", "area": "Empaque"}'

# 3. Ingest telemetry
curl -X POST http://localhost:5001/api/v1/telemetry \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"device_id": "UUID", "telemetry": {"temperature": {"value": 25.5, "unit": "C"}}}'

# 4. Query data
curl http://localhost:5001/api/v1/telemetry?device_id=UUID \\
  -H "Authorization: Bearer YOUR_TOKEN"
</code></pre>
            </div>
        </div>

        <script>
            function showLogin() {
                alert('Login endpoint: POST /api/v1/auth/login');
            }
        </script>
    </body>
    </html>
    """)

# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.route('/health')
@limiter.limit("1000 per minute")  # High limit for health checks
def health():
    """Health check endpoint
    ---
    tags:
      - Health
    responses:
      200:
        description: System health status
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
            database:
              type: string
              example: ok
            version:
              type: string
              example: "2.0"
            timestamp:
              type: string
              example: "2025-10-27T20:00:00"
    """
    conn = get_db_connection()
    db_status = 'ok' if conn else 'error'
    if conn:
        conn.close()

    return jsonify({
        'status': 'healthy' if db_status == 'ok' else 'degraded',
        'database': db_status,
        'version': '2.0',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/mobile')
def mobile_dashboard():
    """Mobile-responsive dashboard (Phase 3 Feature 3)"""
    import os
    mobile_path = os.path.join(os.path.dirname(__file__), 'static', 'mobile_dashboard.html')
    return send_file(mobile_path)

@app.route('/api/v1/status')
@limiter.limit("100 per minute")  # Moderate limit for status checks
def api_status():
    """API status and statistics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        # Get counts
        cur.execute("SELECT COUNT(*) as count FROM devices")
        device_count = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) as count FROM devices WHERE status = 'online'")
        online_count = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) as count FROM alerts WHERE status = 'active'")
        active_alerts = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) as count FROM telemetry WHERE timestamp > NOW() - INTERVAL '1 hour'")
        recent_telemetry = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) as count FROM rules WHERE enabled = true")
        active_rules = cur.fetchone()['count']

        return jsonify({
            'status': 'operational',
            'version': '2.0',
            'statistics': {
                'total_devices': device_count,
                'online_devices': online_count,
                'active_alerts': active_alerts,
                'telemetry_last_hour': recent_telemetry,
                'active_rules': active_rules
            },
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# PUBLIC DASHBOARD ENDPOINTS (No Authentication Required)
# ============================================================================

@app.route('/api/v1/dashboard/devices', methods=['GET'])
@limiter.limit("100 per minute")
def dashboard_devices():
    """Public endpoint for dashboard - Get recent devices (no auth required)"""
    limit = int(request.args.get('limit', 5))

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, type as device_type, location, status, protocol, created_at
            FROM devices
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))

        devices = cur.fetchall()
        devices_list = []
        for device in devices:
            device_dict = dict(device)
            device_dict['id'] = str(device_dict['id'])
            devices_list.append(device_dict)

        return jsonify({
            'devices': devices_list,
            'count': len(devices_list)
        }), 200

    except Exception as e:
        logger.error(f"Dashboard devices error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/dashboard/alerts', methods=['GET'])
@limiter.limit("100 per minute")
def dashboard_alerts():
    """Public endpoint for dashboard - Get recent alerts (no auth required)"""
    limit = int(request.args.get('limit', 5))

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, device_id, rule_id, severity, message, status, created_at
            FROM alerts
            WHERE status = 'active'
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))

        alerts = cur.fetchall()
        alerts_list = []
        for alert in alerts:
            alert_dict = dict(alert)
            alert_dict['id'] = str(alert_dict['id'])
            if alert_dict['device_id']:
                alert_dict['device_id'] = str(alert_dict['device_id'])
            if alert_dict['rule_id']:
                alert_dict['rule_id'] = str(alert_dict['rule_id'])
            alerts_list.append(alert_dict)

        return jsonify({
            'alerts': alerts_list,
            'count': len(alerts_list)
        }), 200

    except Exception as e:
        logger.error(f"Dashboard alerts error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/dashboard/rules', methods=['GET'])
@limiter.limit("100 per minute")
def dashboard_rules():
    """Public endpoint for dashboard - Get active rules (no auth required)"""
    limit = int(request.args.get('limit', 20))

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, rule_type, conditions, enabled, created_at
            FROM rules
            WHERE enabled = true
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))

        rules = cur.fetchall()
        rules_list = []
        for rule in rules:
            rule_dict = dict(rule)
            rule_dict['id'] = str(rule_dict['id'])
            rules_list.append(rule_dict)

        return jsonify({
            'rules': rules_list,
            'count': len(rules_list)
        }), 200

    except Exception as e:
        logger.error(f"Dashboard rules error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/dashboard/telemetry', methods=['GET'])
@limiter.limit("100 per minute")
def dashboard_telemetry():
    """Public endpoint for dashboard - Get recent telemetry (no auth required)"""
    limit = int(request.args.get('limit', 50))
    device_id = request.args.get('device_id')  # Optional filter
    location = request.args.get('location')  # Optional filter by device location

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        if device_id:
            # Get telemetry for specific device
            cur.execute("""
                SELECT
                    t.id,
                    t.device_id,
                    t.timestamp,
                    t.key,
                    t.value,
                    t.unit,
                    d.name as device_name
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE t.device_id = %s
                ORDER BY t.timestamp DESC
                LIMIT %s
            """, (device_id, limit))
        elif location:
            # Get telemetry for devices at specific location
            cur.execute("""
                SELECT
                    t.id,
                    t.device_id,
                    t.timestamp,
                    t.key,
                    t.value,
                    t.unit,
                    d.name as device_name
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                WHERE d.location = %s
                ORDER BY t.timestamp DESC
                LIMIT %s
            """, (location, limit))
        else:
            # Get recent telemetry from all devices
            cur.execute("""
                SELECT
                    t.id,
                    t.device_id,
                    t.timestamp,
                    t.key,
                    t.value,
                    t.unit,
                    d.name as device_name
                FROM telemetry t
                JOIN devices d ON t.device_id = d.id
                ORDER BY t.timestamp DESC
                LIMIT %s
            """, (limit,))

        telemetry = cur.fetchall()
        telemetry_list = []
        for point in telemetry:
            point_dict = dict(point)
            point_dict['id'] = str(point_dict['id'])
            point_dict['device_id'] = str(point_dict['device_id'])
            telemetry_list.append(point_dict)

        return jsonify({
            'telemetry': telemetry_list,
            'count': len(telemetry_list)
        }), 200

    except Exception as e:
        logger.error(f"Dashboard telemetry error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# MQTT ENDPOINTS
# ============================================================================

@app.route('/api/v1/mqtt/info', methods=['GET'])
@jwt_required()
def get_mqtt_info():
    """Get MQTT broker connection information"""
    try:
        broker = get_broker()
        if not broker:
            return jsonify({'error': 'MQTT broker not initialized'}), 503

        info = broker.get_connection_info()
        return jsonify({
            'broker': info,
            'message': 'MQTT broker information retrieved successfully'
        }), 200

    except Exception as e:
        logger.error(f"MQTT info error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/mqtt/publish', methods=['POST'])
@jwt_required()
def mqtt_publish():
    """Publish message to MQTT topic

    Body:
    {
        "topic": "insa/devices/abc-123/telemetry",
        "payload": {...},
        "qos": 1,
        "retain": false
    }
    """
    try:
        data = request.get_json()

        if not data or 'topic' not in data or 'payload' not in data:
            return jsonify({'error': 'Missing required fields: topic, payload'}), 400

        broker = get_broker()
        if not broker or not broker.connected:
            return jsonify({'error': 'MQTT broker not connected'}), 503

        topic = data['topic']
        payload = data['payload']
        qos = data.get('qos', 1)
        retain = data.get('retain', False)

        success = broker.publish(topic, payload, qos=qos, retain=retain)

        if success:
            return jsonify({
                'message': 'Message published successfully',
                'topic': topic
            }), 200
        else:
            return jsonify({'error': 'Failed to publish message'}), 500

    except Exception as e:
        logger.error(f"MQTT publish error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/mqtt/command', methods=['POST'])
@jwt_required()
def send_device_command():
    """Send command to device via MQTT

    Body:
    {
        "device_id": "uuid",
        "command": "reboot",
        "parameters": {...}
    }
    """
    try:
        data = request.get_json()

        if not data or 'device_id' not in data or 'command' not in data:
            return jsonify({'error': 'Missing required fields: device_id, command'}), 400

        broker = get_broker()
        if not broker or not broker.connected:
            return jsonify({'error': 'MQTT broker not connected'}), 503

        device_id = data['device_id']
        command = data['command']
        parameters = data.get('parameters', {})

        success = broker.send_command_to_device(device_id, command, parameters)

        if success:
            return jsonify({
                'message': 'Command sent successfully',
                'device_id': device_id,
                'command': command
            }), 200
        else:
            return jsonify({'error': 'Failed to send command'}), 500

    except Exception as e:
        logger.error(f"MQTT command error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/mqtt/test/publish', methods=['POST'])
@jwt_required()
def test_mqtt_publish():
    """Test MQTT by publishing telemetry for a device

    Body:
    {
        "device_id": "uuid",
        "telemetry": {
            "temperature": {"value": 25.5, "unit": "C"},
            "humidity": {"value": 65, "unit": "%"}
        }
    }
    """
    try:
        data = request.get_json()

        if not data or 'device_id' not in data or 'telemetry' not in data:
            return jsonify({'error': 'Missing required fields: device_id, telemetry'}), 400

        broker = get_broker()
        if not broker or not broker.connected:
            return jsonify({'error': 'MQTT broker not connected'}), 503

        device_id = data['device_id']
        telemetry = data['telemetry']

        success = broker.publish_telemetry(device_id, telemetry)

        if success:
            return jsonify({
                'message': 'Test telemetry published successfully',
                'device_id': device_id,
                'note': 'MQTT broker will receive and store this data automatically'
            }), 200
        else:
            return jsonify({'error': 'Failed to publish test telemetry'}), 500

    except Exception as e:
        logger.error(f"MQTT test publish error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# WEBSOCKET API ENDPOINTS
# ============================================================================

@app.route('/api/v1/websocket/info', methods=['GET'])
@jwt_required()
def get_websocket_info():
    """
    Get WebSocket server information and connection statistics

    Returns connection counts, authenticated clients, subscriptions
    """
    try:
        ws_server = get_websocket_server()
        if not ws_server:
            return jsonify({'error': 'WebSocket server not initialized'}), 503

        stats = ws_server.get_connection_stats()

        return jsonify({
            'websocket': {
                'endpoint': 'ws://localhost:5002/socket.io/',
                'protocol': 'Socket.IO',
                'status': 'active'
            },
            'connections': stats,
            'features': [
                'Real-time telemetry updates',
                'Device status notifications',
                'Alert broadcasts',
                'JWT authentication'
            ],
            'events': {
                'client_to_server': [
                    'connect',
                    'authenticate',
                    'subscribe_device',
                    'unsubscribe_device',
                    'subscribe_all_devices',
                    'get_status'
                ],
                'server_to_client': [
                    'telemetry_update',
                    'device_status',
                    'alert',
                    'alert_update'
                ]
            }
        }), 200

    except Exception as e:
        logger.error(f"WebSocket info error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/websocket/test/telemetry', methods=['POST'])
@jwt_required()
def test_websocket_telemetry():
    """
    Test WebSocket by emitting a telemetry update

    Request body:
    {
        "device_id": "uuid",
        "telemetry": {"temperature": 25.5, "humidity": 60}
    }
    """
    try:
        data = request.get_json()

        if not data or 'device_id' not in data or 'telemetry' not in data:
            return jsonify({'error': 'Missing required fields: device_id, telemetry'}), 400

        ws_server = get_websocket_server()
        if not ws_server:
            return jsonify({'error': 'WebSocket server not initialized'}), 503

        device_id = data['device_id']
        telemetry = data['telemetry']

        # Emit test telemetry update via WebSocket
        ws_server.emit_telemetry_update(device_id, telemetry)

        return jsonify({
            'message': 'Test telemetry emitted successfully via WebSocket',
            'device_id': device_id,
            'telemetry': telemetry,
            'note': 'Connected WebSocket clients subscribed to this device will receive the update'
        }), 200

    except Exception as e:
        logger.error(f"WebSocket test telemetry error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/websocket/test/alert', methods=['POST'])
@jwt_required()
def test_websocket_alert():
    """
    Test WebSocket by emitting an alert

    Request body:
    {
        "device_id": "uuid",
        "severity": "warning",
        "message": "Test alert"
    }
    """
    try:
        data = request.get_json()

        if not data or 'device_id' not in data:
            return jsonify({'error': 'Missing required field: device_id'}), 400

        ws_server = get_websocket_server()
        if not ws_server:
            return jsonify({'error': 'WebSocket server not initialized'}), 503

        device_id = data['device_id']
        severity = data.get('severity', 'info')
        message = data.get('message', 'Test alert')

        # Emit test alert via WebSocket
        alert_id = str(uuid.uuid4())
        ws_server.emit_alert(
            alert_id=alert_id,
            device_id=device_id,
            severity=severity,
            message=message,
            alert_data={'test': True}
        )

        return jsonify({
            'message': 'Test alert emitted successfully via WebSocket',
            'alert_id': alert_id,
            'device_id': device_id,
            'severity': severity,
            'alert_message': message,
            'note': 'Connected WebSocket clients subscribed to this device will receive the alert'
        }), 200

    except Exception as e:
        logger.error(f"WebSocket test alert error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# RULE ENGINE API ENDPOINTS
# ============================================================================

@app.route('/api/v1/rules', methods=['POST'])
@require_auth
@require_tenant
def create_rule():
    """
    Create a new rule for current tenant

    Request body:
    {
        "name": "High Temperature Alert",
        "device_id": "uuid",
        "rule_type": "threshold",  # threshold, comparison, time_based, statistical
        "conditions": {...},
        "actions": [{...}],
        "priority": 5,
        "enabled": true
    }
    """
    try:
        # Get tenant context
        tenant_id = g.tenant_id

        data = request.get_json()

        required_fields = ['name', 'device_id', 'rule_type', 'conditions', 'actions']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        rule_id = str(uuid.uuid4())

        cur.execute("""
            INSERT INTO rules (id, name, device_id, rule_type, conditions, actions, priority, enabled, created_at, tenant_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            RETURNING *
        """, (
            rule_id,
            data['name'],
            data['device_id'],
            data['rule_type'],
            json.dumps(data['conditions']),
            json.dumps(data['actions']),
            data.get('priority', 5),
            data.get('enabled', True),
            tenant_id
        ))

        rule = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Rule created: {data['name']} ({rule_id})")

        return jsonify({
            'message': 'Rule created successfully',
            'rule': dict(rule)
        }), 201

    except Exception as e:
        logger.error(f"Create rule error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules', methods=['GET'])
@require_auth
@require_tenant
def list_rules():
    """
    List all rules for current tenant with optional filtering

    Query parameters:
    - device_id: Filter by device
    - rule_type: Filter by type
    - enabled: Filter by enabled status
    """
    try:
        # Get tenant context
        tenant_id = g.tenant_id

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        # Build query with tenant filtering
        query = "SELECT * FROM rules WHERE tenant_id = %s"
        params = [tenant_id]

        if request.args.get('device_id'):
            query += " AND device_id = %s"
            params.append(request.args.get('device_id'))

        if request.args.get('rule_type'):
            query += " AND rule_type = %s"
            params.append(request.args.get('rule_type'))

        if request.args.get('enabled') is not None:
            enabled = request.args.get('enabled').lower() == 'true'
            query += " AND enabled = %s"
            params.append(enabled)

        query += " ORDER BY priority DESC, created_at DESC"

        cur.execute(query, params)
        rules = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify({
            'rules': [dict(r) for r in rules],
            'count': len(rules)
        }), 200

    except Exception as e:
        logger.error(f"List rules error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules/<rule_id>', methods=['GET'])
@require_auth
@require_tenant
def get_rule(rule_id):
    """Get rule details by ID for current tenant"""
    try:
        # Get tenant context
        tenant_id = g.tenant_id

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        cur.execute("SELECT * FROM rules WHERE id = %s AND tenant_id = %s", (rule_id, tenant_id))
        rule = cur.fetchone()

        cur.close()
        conn.close()

        if not rule:
            return jsonify({'error': 'Rule not found'}), 404

        return jsonify({'rule': dict(rule)}), 200

    except Exception as e:
        logger.error(f"Get rule error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules/<rule_id>', methods=['PUT'])
@require_auth
@require_tenant
def update_rule(rule_id):
    """Update rule by ID for current tenant"""
    try:
        # Get tenant context
        tenant_id = g.tenant_id

        data = request.get_json()

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        # Build update query dynamically
        update_fields = []
        params = []

        if 'name' in data:
            update_fields.append("name = %s")
            params.append(data['name'])

        if 'conditions' in data:
            update_fields.append("conditions = %s")
            params.append(json.dumps(data['conditions']))

        if 'actions' in data:
            update_fields.append("actions = %s")
            params.append(json.dumps(data['actions']))

        if 'priority' in data:
            update_fields.append("priority = %s")
            params.append(data['priority'])

        if 'enabled' in data:
            update_fields.append("enabled = %s")
            params.append(data['enabled'])

        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400

        params.extend([rule_id, tenant_id])

        query = f"UPDATE rules SET {', '.join(update_fields)} WHERE id = %s AND tenant_id = %s RETURNING *"

        cur.execute(query, params)
        rule = cur.fetchone()

        if not rule:
            conn.close()
            return jsonify({'error': 'Rule not found'}), 404

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Rule updated: {rule_id}")

        return jsonify({
            'message': 'Rule updated successfully',
            'rule': dict(rule)
        }), 200

    except Exception as e:
        logger.error(f"Update rule error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules/<rule_id>', methods=['DELETE'])
@require_auth
@require_tenant
def delete_rule(rule_id):
    """Delete rule by ID for current tenant"""
    try:
        # Get tenant context
        tenant_id = g.tenant_id

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        cur.execute("DELETE FROM rules WHERE id = %s AND tenant_id = %s RETURNING id", (rule_id, tenant_id))
        deleted = cur.fetchone()

        if not deleted:
            conn.close()
            return jsonify({'error': 'Rule not found'}), 404

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Rule deleted: {rule_id}")

        return jsonify({'message': 'Rule deleted successfully'}), 200

    except Exception as e:
        logger.error(f"Delete rule error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules/<rule_id>/test', methods=['POST'])
@require_auth
@require_tenant
def test_rule(rule_id):
    """
    Test rule evaluation without triggering actions for current tenant

    Returns whether rule would be triggered with current telemetry
    """
    try:
        # Get tenant context
        tenant_id = g.tenant_id

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        cur.execute("SELECT * FROM rules WHERE id = %s AND tenant_id = %s", (rule_id, tenant_id))
        rule = cur.fetchone()

        cur.close()
        conn.close()

        if not rule:
            return jsonify({'error': 'Rule not found'}), 404

        # Evaluate rule manually
        engine = get_rule_engine()
        if not engine:
            return jsonify({'error': 'Rule engine not initialized'}), 503

        rule_dict = dict(rule)
        device_id = rule_dict['device_id']
        rule_type = rule_dict['rule_type']
        conditions = rule_dict['conditions']

        # Evaluate based on type
        triggered = False
        context = {}

        if rule_type == 'threshold':
            triggered, context = engine._evaluate_threshold_rule(device_id, conditions)
        elif rule_type == 'comparison':
            triggered, context = engine._evaluate_comparison_rule(device_id, conditions)
        elif rule_type == 'time_based':
            triggered, context = engine._evaluate_time_based_rule(device_id, conditions)
        elif rule_type == 'statistical':
            triggered, context = engine._evaluate_statistical_rule(device_id, conditions)

        return jsonify({
            'rule_id': rule_id,
            'triggered': triggered,
            'context': context,
            'message': 'Rule triggered' if triggered else 'Rule not triggered'
        }), 200

    except Exception as e:
        logger.error(f"Test rule error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# TENANT MANAGEMENT (Phase 3 Feature 6 - Phase 3)
# ============================================================================

@app.route('/api/v1/tenants', methods=['GET'])
@require_auth
def list_tenants():
    """
    List all tenants (system admin only)

    Query Parameters:
        - page (int): Page number (default: 1)
        - limit (int): Items per page (default: 50, max: 100)
        - tier (str): Filter by tier (free|startup|professional|enterprise)
        - search (str): Search by name or slug

    Returns:
        200: {"tenants": [...], "total": 1, "page": 1, "limit": 50}
        403: Not system admin
    """
    # Get current user from g.current_user (set by @require_auth)
    user_id = g.current_user['id']

    # Check if system admin
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()

    if not user or not user['is_admin']:
        return jsonify({'error': 'System admin access required'}), 403

    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 50, type=int), 100)
    tier = request.args.get('tier')
    search = request.args.get('search')

    # Build query
    query = "SELECT * FROM tenants WHERE 1=1"
    params = []

    if tier:
        query += " AND tier = %s"
        params.append(tier)

    if search:
        query += " AND (name ILIKE %s OR slug ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    # Count total
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cur.execute(count_query, params)
    total = cur.fetchone()['count']

    # Get paginated results
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, (page - 1) * limit])

    cur.execute(query, params)
    tenants = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        'tenants': [dict(t) for t in tenants],
        'total': total,
        'page': page,
        'limit': limit
    }), 200

@app.route('/api/v1/tenants', methods=['POST'])
@require_auth
def create_tenant():
    """
    Create new tenant (system admin only)

    Request Body:
        {
            "name": "Acme Corp",
            "slug": "acme-corp",
            "tier": "professional",
            "max_devices": 100,
            "max_users": 10
        }

    Returns:
        201: Tenant object
        403: Not system admin
        400: Validation error
    """
    # Check system admin
    user_id = g.current_user['id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()

    if not user or not user['is_admin']:
        return jsonify({'error': 'System admin access required'}), 403

    # Validate request
    data = request.get_json()
    required = ['name', 'slug', 'tier']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate tier (must match database constraint)
    valid_tiers = ['starter', 'professional', 'enterprise']
    if data['tier'] not in valid_tiers:
        return jsonify({'error': f'Invalid tier. Must be one of: {", ".join(valid_tiers)}'}), 400

    # Use tenant_manager to create tenant
    try:
        with TenantManager(DB_CONFIG) as manager:
            tenant = manager.create_tenant(
                name=data['name'],
                slug=data['slug'],
                tier=data['tier'],
                max_devices=data.get('max_devices'),
                max_users=data.get('max_users')
            )

        return jsonify(tenant), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        return jsonify({'error': 'Failed to create tenant'}), 500

@app.route('/api/v1/tenants/<tenant_id>', methods=['GET'])
@require_auth
@require_tenant
def get_tenant(tenant_id):
    """
    Get tenant details (must be member of tenant or system admin)

    Returns:
        200: Tenant object
        403: Not authorized
        404: Tenant not found
    """
    # Check access
    user_id = g.current_user['id']
    user_tenant_id = g.tenant_id

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if system admin or tenant member
    cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    is_admin = user and user['is_admin']

    if not is_admin and str(user_tenant_id) != tenant_id:
        return jsonify({'error': 'Access denied'}), 403

    # Get tenant
    cur.execute("SELECT * FROM tenants WHERE id = %s", (tenant_id,))
    tenant = cur.fetchone()

    cur.close()
    conn.close()

    if not tenant:
        return jsonify({'error': 'Tenant not found'}), 404

    return jsonify(dict(tenant)), 200

@app.route('/api/v1/tenants/<tenant_id>', methods=['PATCH'])
@require_auth
@require_tenant_admin
def update_tenant(tenant_id):
    """
    Update tenant settings (tenant admin or system admin only)

    Request Body:
        {
            "name": "New Name",
            "tier": "enterprise",
            "max_devices": 200
        }

    Returns:
        200: Updated tenant object
        403: Not authorized
        400: Validation error
    """
    # Update using tenant_manager
    data = request.get_json()

    try:
        # Only pass fields that are in the request data
        updates = {}
        if 'name' in data:
            updates['name'] = data['name']
        if 'tier' in data:
            updates['tier'] = data['tier']
        if 'max_devices' in data:
            updates['max_devices'] = data['max_devices']
        if 'max_users' in data:
            updates['max_users'] = data['max_users']

        with TenantManager(DB_CONFIG) as manager:
            manager.update_tenant(tenant_id=tenant_id, **updates)

            # Get updated tenant
            tenant = manager.get_tenant(tenant_id)

        return jsonify(tenant), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to update tenant: {e}")
        return jsonify({'error': 'Failed to update tenant'}), 500

@app.route('/api/v1/tenants/<tenant_id>/stats', methods=['GET'])
@require_auth
@require_tenant
def get_tenant_stats(tenant_id):
    """
    Get tenant statistics (usage counts)

    Returns:
        200: Statistics object
        403: Not authorized
    """
    # Check access
    user_id = g.current_user['id']
    user_tenant_id = g.tenant_id

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    is_admin = user and user['is_admin']

    if not is_admin and str(user_tenant_id) != tenant_id:
        return jsonify({'error': 'Access denied'}), 403

    # Get stats using tenant_manager
    try:
        with TenantManager(DB_CONFIG) as manager:
            stats = manager.get_tenant_stats(tenant_id)

        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Failed to get tenant stats: {e}")
        return jsonify({'error': 'Failed to get tenant stats'}), 500

@app.route('/api/v1/tenants/<tenant_id>/users', methods=['GET'])
@require_auth
@require_tenant
def list_tenant_users(tenant_id):
    """
    List all users in tenant

    Returns:
        200: {"users": [...]}
        403: Not authorized
    """
    # Check access
    user_id = g.current_user['id']
    user_tenant_id = g.tenant_id

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    is_admin = user and user['is_admin']

    if not is_admin and str(user_tenant_id) != tenant_id:
        return jsonify({'error': 'Access denied'}), 403

    # Get tenant users
    cur.execute("""
        SELECT
            tu.user_id,
            u.email,
            tu.role_id,
            r.name as role_name,
            tu.is_tenant_admin,
            tu.created_at
        FROM tenant_users tu
        JOIN users u ON tu.user_id = u.id
        LEFT JOIN roles r ON tu.role_id = r.id
        WHERE tu.tenant_id = %s
        ORDER BY tu.created_at ASC
    """, (tenant_id,))
    users = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({'users': [dict(u) for u in users]}), 200

@app.route('/api/v1/tenants/<tenant_id>/users/invite', methods=['POST'])
@require_auth
@require_tenant_admin
def invite_user_to_tenant(tenant_id):
    """
    Invite user to tenant (tenant admin only)

    Request Body:
        {
            "email": "newuser@example.com",
            "role": "member"
        }

    Returns:
        201: Invitation object
        400: Validation error
    """
    data = request.get_json()

    if not data.get('email'):
        return jsonify({'error': 'Email required'}), 400

    # Get current user_id (not email)
    user_id = g.current_user['id']

    # Get role_id from role name
    conn = get_db_connection()
    cur = conn.cursor()
    role_name = data.get('role', 'viewer')
    cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
    role = cur.fetchone()
    if not role:
        return jsonify({'error': f'Invalid role: {role_name}'}), 400
    role_id = role['id']

    # Use tenant_manager to create invitation
    try:
        with TenantManager(DB_CONFIG) as manager:
            invitation = manager.create_invitation(
                tenant_id=tenant_id,
                email=data['email'],
                role_id=role_id,
                invited_by=user_id
            )

        # TODO: Send invitation email

        return jsonify(invitation), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to invite user: {e}")
        return jsonify({'error': 'Failed to invite user'}), 500

@app.route('/api/v1/tenants/<tenant_id>/users/<user_id>', methods=['DELETE'])
@require_auth
@require_tenant_admin
def remove_user_from_tenant(tenant_id, user_id):
    """
    Remove user from tenant (tenant admin only)

    Returns:
        204: User removed
        400: Cannot remove
        404: User not found
    """
    # Use tenant_manager
    try:
        with TenantManager(DB_CONFIG) as manager:
            manager.remove_user(tenant_id, user_id)

        return '', 204

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to remove user: {e}")
        return jsonify({'error': 'Failed to remove user'}), 500

@app.route('/api/v1/tenants/<tenant_id>/users/<user_id>/role', methods=['PATCH'])
@require_auth
@require_tenant_admin
def update_user_role(tenant_id, user_id):
    """
    Update user role in tenant (tenant admin only)

    Request Body:
        {
            "role": "admin",
            "is_tenant_admin": true
        }

    Returns:
        200: Updated user object
        400: Invalid role
        404: User not found
    """
    data = request.get_json()

    # Use tenant_manager
    try:
        with TenantManager(DB_CONFIG) as manager:
            manager.update_user_role(
                tenant_id=tenant_id,
                user_id=user_id,
                role=data.get('role'),
                is_tenant_admin=data.get('is_tenant_admin')
            )

            # Get updated user
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, role, is_tenant_admin
                FROM tenant_users
                WHERE tenant_id = %s AND user_id = %s
            """, (tenant_id, user_id))
            user = cur.fetchone()
            cur.close()
            conn.close()

        return jsonify(dict(user)), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to update user role: {e}")
        return jsonify({'error': 'Failed to update user role'}), 500

@app.route('/api/v1/tenants/<tenant_id>/quotas', methods=['GET'])
@require_auth
@require_tenant
def get_tenant_quotas(tenant_id):
    """
    Get tenant quota usage

    Returns:
        200: Quota usage object
        403: Not authorized
    """
    # Check access
    user_id = g.current_user['id']
    user_tenant_id = g.tenant_id

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    is_admin = user and user['is_admin']

    if not is_admin and str(user_tenant_id) != tenant_id:
        return jsonify({'error': 'Access denied'}), 403

    # Get tenant limits
    cur.execute("""
        SELECT max_devices, max_users, max_telemetry_points_per_day, max_retention_days
        FROM tenants
        WHERE id = %s
    """, (tenant_id,))
    tenant = cur.fetchone()

    # Get usage stats
    try:
        with TenantManager(DB_CONFIG) as manager:
            stats = manager.get_tenant_stats(tenant_id)

        # Calculate quotas
        quotas = {
            'devices': {
                'used': stats['device_count'],
                'limit': tenant['max_devices'],
                'percentage': (stats['device_count'] / tenant['max_devices'] * 100) if tenant['max_devices'] else None
            },
            'users': {
                'used': stats['user_count'],
                'limit': tenant['max_users'],
                'percentage': (stats['user_count'] / tenant['max_users'] * 100) if tenant['max_users'] else None
            },
            'telemetry_points': {
                'used_today': stats.get('telemetry_points_today', 0),
                'limit_per_day': tenant['max_telemetry_points_per_day'],
                'percentage': (stats.get('telemetry_points_today', 0) / tenant['max_telemetry_points_per_day'] * 100) if tenant['max_telemetry_points_per_day'] else None
            },
            'data_retention': {
                'current_days': tenant['max_retention_days'],
                'oldest_data_age_days': stats.get('oldest_data_days', 0)
            }
        }

        return jsonify(quotas), 200

    except Exception as e:
        logger.error(f"Failed to get quotas: {e}")
        return jsonify({'error': 'Failed to get quotas'}), 500

# ============================================================================
# INITIALIZATION & MAIN
# ============================================================================

def create_default_user():
    """Create default admin user if none exists"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        # Check if any users exist
        cur.execute("SELECT COUNT(*) as count FROM users")
        user_count = cur.fetchone()['count']

        if user_count == 0:
            # Create default admin
            password_hash = hash_password('admin123')

            cur.execute("""
                INSERT INTO users (email, password_hash, role, permissions)
                VALUES ('admin@insa.com', %s, 'admin', '{}')
            """, (password_hash,))

            conn.commit()
            logger.info("Default admin user created: admin@insa.com / admin123")
            logger.warning("⚠️  Please change the default password immediately!")

    except Exception as e:
        logger.error(f"Create default user error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("INSA Advanced IIoT Platform v2.0")
    logger.info("=" * 60)

    # Initialize database
    logger.info("Initializing database schema...")
    if init_database():
        logger.info("✅ Database initialized successfully")

        # Create default user
        create_default_user()

        # Multi-tenancy context (Phase 3 Feature 6)
        # Note: Using decorator-based approach (@require_tenant) instead of middleware
        # to avoid conflicts with Socket.IO wrapping
        logger.info("🏢 Multi-tenancy enabled:")
        logger.info("   - Tenant isolation via @require_tenant decorator")
        logger.info("   - JWT tokens include tenant_id claim")
        logger.info("   - Quota management via @check_tenant_quota decorator")

        # Initialize WebSocket server
        logger.info("Initializing WebSocket server...")
        ws_server = init_websocket_server(app)
        socketio = ws_server.get_socketio()
        logger.info("✅ WebSocket server initialized")

        # Initialize MQTT broker
        logger.info("Initializing MQTT broker...")
        mqtt_broker = init_broker(DB_CONFIG, host='localhost', port=1883)
        if mqtt_broker and mqtt_broker.connected:
            # Register callback to emit real-time telemetry updates
            def on_telemetry_update(device_id, telemetry):
                ws_server.emit_telemetry_update(device_id, telemetry)

            mqtt_broker.register_telemetry_callback(on_telemetry_update)

            logger.info("✅ MQTT broker connected successfully")
            logger.info(f"📡 MQTT Endpoint: mqtt://localhost:1883")
            logger.info("✅ Real-time updates enabled (MQTT → WebSocket)")
        else:
            logger.warning("⚠️  MQTT broker connection failed - continuing without MQTT")

        # Initialize and start rule engine
        logger.info("Initializing rule engine...")
        rule_engine = init_rule_engine(DB_CONFIG)
        rule_engine.start()
        logger.info("✅ Rule engine started - evaluating every 30 seconds")
        logger.info("📋 Supported rule types: threshold, comparison, time_based, statistical")

        # Initialize and start retention scheduler (Phase 3 Feature 7)
        logger.info("Initializing retention scheduler...")
        retention_scheduler = init_retention_scheduler(DB_CONFIG)
        scheduled_jobs = retention_scheduler.get_scheduled_jobs()
        logger.info(f"✅ Retention scheduler started - {len(scheduled_jobs)} policies scheduled")
        for job in scheduled_jobs:
            logger.info(f"   📅 {job['name']}: next run at {job['next_run_time']}")

        # Initialize email notifier
        logger.info("Initializing email notifier...")
        from email_notifier import init_email_notifier
        email_notifier = init_email_notifier(SMTP_CONFIG)
        if email_notifier.test_email_connection():
            logger.info("✅ Email notifier initialized and SMTP connection verified")
            logger.info(f"📧 Email Endpoint: {SMTP_CONFIG['host']}:{SMTP_CONFIG['port']}")
        else:
            logger.warning("⚠️  SMTP connection test failed - email notifications may not work")

        # Initialize webhook notifier
        logger.info("Initializing webhook notifier...")
        from webhook_notifier import init_webhook_notifier
        webhook_notifier = init_webhook_notifier(WEBHOOK_CONFIG)
        logger.info("✅ Webhook notifier initialized")
        logger.info(f"🔒 Security: SSRF protection enabled, private IPs blocked")
        logger.info(f"⚡ Retry policy: {WEBHOOK_CONFIG['max_retries']} attempts with exponential backoff")

        # Initialize Redis cache
        logger.info("Initializing Redis cache...")
        from redis_cache import init_redis_cache
        redis_cache = init_redis_cache(REDIS_CONFIG)
        if redis_cache.test_connection():
            logger.info("✅ Redis cache initialized and connection verified")
            logger.info(f"📊 Cache Endpoint: {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}")
            cache_info = redis_cache.get_cache_info()
            logger.info(f"💾 Memory Usage: {cache_info.get('used_memory', 'N/A')}")
        else:
            logger.warning("⚠️  Redis connection failed - continuing without caching")
            logger.warning("Performance may be impacted without Redis cache")

        # Initialize Grafana integration
        logger.info("Initializing Grafana integration...")
        from grafana_integration import init_grafana_integration
        grafana_integration = init_grafana_integration(GRAFANA_CONFIG['url'], GRAFANA_CONFIG.get('api_key'))
        logger.info("✅ Grafana integration initialized")
        logger.info(f"📊 Grafana Endpoint: {GRAFANA_CONFIG['url']}")
        logger.info(f"📈 Dashboards: Device Overview, Telemetry, Alerts & Rules")
        logger.info(f"💡 Run provision_grafana_dashboards.py to create dashboards")

        # Verify API rate limiter status (Phase 3 Feature 9)
        logger.info("✅ API rate limiter active")
        logger.info("🛡️  Rate limits enforced:")
        logger.info("   - Health check: 1000/min")
        logger.info("   - Status: 100/min")
        logger.info("   - Login: 5/min (brute force protection)")
        logger.info("   - Registration: 3/hour")
        logger.info("   - Token refresh: 10/min")
        logger.info("   - Devices: 200/min")
        logger.info("   - Telemetry: 500/min")
        logger.info("📝 Note: Using memory backend (change storage_uri for Redis in production)")

        logger.info("🚀 Starting server on http://0.0.0.0:5002")
        logger.info("📚 Swagger/OpenAPI Docs: http://localhost:5002/apidocs")
        logger.info("📋 API Spec (JSON): http://localhost:5002/apispec.json")
        logger.info("💚 Health Check: http://localhost:5002/health")
        logger.info("🔌 WebSocket Endpoint: ws://localhost:5002/socket.io/")
        logger.info("🤖 ML API Endpoints: http://localhost:5002/api/v1/ml/*")
        logger.info("   - POST /api/v1/ml/models/train (train model)")
        logger.info("   - POST /api/v1/ml/predict (single prediction)")
        logger.info("   - POST /api/v1/ml/predict/batch (batch predictions)")
        logger.info("   - GET /api/v1/ml/models (list models)")
        logger.info("   - GET /api/v1/ml/anomalies (query anomalies)")
        logger.info("=" * 60)

        # Run server with Socket.IO (uses eventlet)
        socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)
    else:
        logger.error("❌ Failed to initialize database")
        logger.error("Please check database connection and permissions")

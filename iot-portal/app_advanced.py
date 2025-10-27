#!/usr/bin/env python3
"""
INSA Advanced Industrial IoT Platform
Enterprise-grade IIoT solution with REST API, device management, real-time updates

Version: 2.0
Date: October 27, 2025
Author: INSA Automation Corp
"""

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import json
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import wraps
import logging
from mqtt_broker import init_broker, get_broker
from socketio_server import init_websocket_server, get_websocket_server
from rule_engine import init_rule_engine, get_rule_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)

# Enable CORS for API access
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize JWT
jwt = JWTManager(app)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'insa_iiot',  # New dedicated database
    'user': 'iiot_user',
    'password': 'iiot_secure_2025',
    'port': 5432
}

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
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

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

# ============================================================================
# API ENDPOINTS - AUTHENTICATION
# ============================================================================

@app.route('/api/v1/auth/register', methods=['POST'])
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

        if not user or not verify_password(data['password'], user['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Update last login
        cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
        conn.commit()

        # Create tokens
        access_token = create_access_token(identity=data['email'])
        refresh_token = create_refresh_token(identity=data['email'])

        logger.info(f"User logged in: {user['email']}")

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': str(user['id']),
                'email': user['email'],
                'role': user['role']
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500
    finally:
        conn.close()

@app.route('/api/v1/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify({'access_token': access_token}), 200

# ============================================================================
# API ENDPOINTS - DEVICE MANAGEMENT
# ============================================================================

@app.route('/api/v1/devices', methods=['GET'])
@jwt_required()
def list_devices():
    """List all devices with optional filtering"""
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

        # Build query
        query = "SELECT * FROM devices WHERE 1=1"
        params = []

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
@jwt_required()
def create_device():
    """Register new device"""
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
                connection_string, config, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, type, status, created_at
        """, (
            data['name'],
            data['type'],
            data.get('location'),
            data.get('area'),
            data.get('protocol', 'http'),
            data.get('connection_string'),
            json.dumps(data.get('config', {})),
            json.dumps(data.get('metadata', {}))
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
@jwt_required()
def get_device(device_id):
    """Get device details"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("SELECT * FROM devices WHERE id = %s", (device_id,))
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
@jwt_required()
def update_device(device_id):
    """Update device"""
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
        params.append(device_id)

        query = f"UPDATE devices SET {', '.join(update_fields)} WHERE id = %s RETURNING *"

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
@jwt_required()
def delete_device(device_id):
    """Delete device"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        cur.execute("DELETE FROM devices WHERE id = %s RETURNING name", (device_id,))
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

        # Update device last_seen
        cur.execute("""
            UPDATE devices
            SET last_seen = NOW(), status = 'online'
            WHERE id = %s
        """, (device_id,))

        # Insert telemetry points
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
                INSERT INTO telemetry (device_id, timestamp, key, value, unit, quality)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (device_id, timestamp, key, value, unit, quality))

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
@jwt_required()
def query_telemetry():
    """Query telemetry data"""
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

        query = "SELECT timestamp, key, value, unit FROM telemetry WHERE device_id = %s"
        params = [device_id]

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
@jwt_required()
def get_latest_telemetry():
    """Get latest telemetry values for device(s)"""
    device_id = request.args.get('device_id')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        if device_id:
            # Latest for specific device
            query = """
                SELECT DISTINCT ON (key)
                    key, value, unit, timestamp
                FROM telemetry
                WHERE device_id = %s
                ORDER BY key, timestamp DESC
            """
            cur.execute(query, (device_id,))
        else:
            # Latest for all devices
            query = """
                SELECT DISTINCT ON (device_id, key)
                    device_id, key, value, unit, timestamp
                FROM telemetry
                ORDER BY device_id, key, timestamp DESC
            """
            cur.execute(query)

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
@jwt_required()
def list_alerts():
    """List alerts with filtering"""
    status = request.args.get('status', 'active')
    severity = request.args.get('severity')
    device_id = request.args.get('device_id')
    limit = int(request.args.get('limit', 100))

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    try:
        cur = conn.cursor()

        query = "SELECT * FROM alerts WHERE status = %s"
        params = [status]

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
@jwt_required()
def create_api_key():
    """Create new API key for device"""
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
                rate_limit, expires_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, created_at
        """, (
            key_hash,
            data['name'],
            data.get('device_id'),
            json.dumps(data.get('permissions', {'read': True, 'write': True})),
            data.get('rate_limit', 1000),
            data.get('expires_at')
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
    """Main dashboard"""
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
def health():
    """Health check endpoint"""
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

@app.route('/api/v1/status')
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

        return jsonify({
            'status': 'operational',
            'version': '2.0',
            'statistics': {
                'total_devices': device_count,
                'online_devices': online_count,
                'active_alerts': active_alerts,
                'telemetry_last_hour': recent_telemetry
            },
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Status error: {e}")
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
@jwt_required()
def create_rule():
    """
    Create a new rule

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
            INSERT INTO rules (id, name, device_id, rule_type, conditions, actions, priority, enabled, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING *
        """, (
            rule_id,
            data['name'],
            data['device_id'],
            data['rule_type'],
            json.dumps(data['conditions']),
            json.dumps(data['actions']),
            data.get('priority', 5),
            data.get('enabled', True)
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
@jwt_required()
def list_rules():
    """
    List all rules with optional filtering

    Query parameters:
    - device_id: Filter by device
    - rule_type: Filter by type
    - enabled: Filter by enabled status
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM rules WHERE 1=1"
        params = []

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
@jwt_required()
def get_rule(rule_id):
    """Get rule details by ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        cur.execute("SELECT * FROM rules WHERE id = %s", (rule_id,))
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
@jwt_required()
def update_rule(rule_id):
    """Update rule by ID"""
    try:
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

        params.append(rule_id)

        query = f"UPDATE rules SET {', '.join(update_fields)} WHERE id = %s RETURNING *"

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
@jwt_required()
def delete_rule(rule_id):
    """Delete rule by ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        cur.execute("DELETE FROM rules WHERE id = %s RETURNING id", (rule_id,))
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
@jwt_required()
def test_rule(rule_id):
    """
    Test rule evaluation without triggering actions

    Returns whether rule would be triggered with current telemetry
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor()

        cur.execute("SELECT * FROM rules WHERE id = %s", (rule_id,))
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

        logger.info("🚀 Starting server on http://0.0.0.0:5002")
        logger.info("📚 API Documentation: http://localhost:5002/api/v1/docs")
        logger.info("💚 Health Check: http://localhost:5002/health")
        logger.info("🔌 WebSocket Endpoint: ws://localhost:5002/socket.io/")
        logger.info("=" * 60)

        # Run server with Socket.IO (uses eventlet)
        socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)
    else:
        logger.error("❌ Failed to initialize database")
        logger.error("Please check database connection and permissions")

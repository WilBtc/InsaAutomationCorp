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
                condition JSONB NOT NULL,
                action JSONB NOT NULL,
                enabled BOOLEAN DEFAULT true,
                priority INTEGER DEFAULT 50,
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

        logger.info("🚀 Starting server on http://0.0.0.0:5002")
        logger.info("📚 API Documentation: http://localhost:5002/api/v1/docs")
        logger.info("💚 Health Check: http://localhost:5002/health")
        logger.info("=" * 60)

        # Run server
        app.run(host='0.0.0.0', port=5002, debug=False)
    else:
        logger.error("❌ Failed to initialize database")
        logger.error("Please check database connection and permissions")

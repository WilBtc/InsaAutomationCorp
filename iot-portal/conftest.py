#!/usr/bin/env python3
"""
INSA Advanced IIoT Platform - Pytest Configuration & Fixtures
Version: 2.0
Updated: October 28, 2025
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import json
from datetime import datetime
from unittest.mock import Mock, MagicMock
import os

# Import app modules
from app_advanced import app as flask_app


# ============================================================================
# Application Fixtures
# ============================================================================

@pytest.fixture(scope='session')
def app():
    """Create Flask application for testing"""
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret-key',
        'RATELIMIT_ENABLED': False,  # Disable rate limiting in tests
    })

    yield flask_app


@pytest.fixture(scope='function')
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create Flask CLI runner"""
    return app.test_cli_runner()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope='session')
def db_connection():
    """Create test database connection"""
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='insa_iiot_test',  # Use separate test database
        user='iiot_user',
        password='iiot_secure_2025'
    )
    yield conn
    conn.close()


@pytest.fixture(scope='function')
def db_cursor(db_connection):
    """Create database cursor with automatic rollback"""
    db_connection.autocommit = False
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    yield cursor
    db_connection.rollback()
    cursor.close()


@pytest.fixture(scope='function')
def mock_db_connection(monkeypatch):
    """Mock database connection for unit tests"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    def mock_get_db():
        return mock_conn

    monkeypatch.setattr('app_advanced.get_db_connection', mock_get_db)
    return mock_conn, mock_cursor


# ============================================================================
# Redis Cache Fixtures
# ============================================================================

@pytest.fixture(scope='session')
def redis_client():
    """Create Redis client for testing"""
    client = redis.Redis(
        host='localhost',
        port=6379,
        db=15,  # Use separate test database (0-15)
        decode_responses=True
    )
    yield client
    client.flushdb()  # Clean up after all tests
    client.close()


@pytest.fixture(scope='function')
def mock_redis_client(monkeypatch):
    """Mock Redis client for unit tests"""
    mock_client = MagicMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = False

    return mock_client


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def admin_token(client):
    """Generate admin JWT token for testing"""
    response = client.post('/api/v1/auth/login', json={
        'email': 'admin@insa.com',
        'password': 'Admin123!'
    })

    if response.status_code == 200:
        data = response.get_json()
        return data['access_token']
    return None


@pytest.fixture(scope='function')
def viewer_token(client):
    """Generate viewer JWT token for testing"""
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@insa.com',
        'password': 'Test123!'
    })

    if response.status_code == 200:
        data = response.get_json()
        return data['access_token']
    return None


@pytest.fixture(scope='function')
def auth_headers(admin_token):
    """Generate authorization headers"""
    return {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_device():
    """Sample device data"""
    return {
        'device_id': 'TEST-DEVICE-001',
        'device_name': 'Test Device',
        'device_type': 'sensor',
        'location': 'Test Lab',
        'status': 'active',
        'metadata': {'manufacturer': 'Test Corp'}
    }


@pytest.fixture
def sample_telemetry():
    """Sample telemetry data"""
    return {
        'device_id': 'TEST-DEVICE-001',
        'metric_name': 'temperature',
        'value': 25.5,
        'unit': '°C',
        'timestamp': datetime.now().isoformat(),
        'quality': 'good'
    }


@pytest.fixture
def sample_rule():
    """Sample rule data"""
    return {
        'rule_name': 'Test Temperature Alert',
        'device_id': 'TEST-DEVICE-001',
        'metric_name': 'temperature',
        'condition': 'greater_than',
        'threshold': 30.0,
        'action': 'email',
        'enabled': True
    }


@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        'email': 'testuser@insa.com',
        'password': 'Test123!',
        'full_name': 'Test User',
        'role': 'developer'
    }


# ============================================================================
# MQTT Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def mock_mqtt_client(monkeypatch):
    """Mock MQTT client for testing"""
    mock_client = MagicMock()
    mock_client.connect.return_value = 0
    mock_client.publish.return_value = (0, 1)
    mock_client.subscribe.return_value = (0, 1)

    return mock_client


# ============================================================================
# Webhook Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def mock_webhook_response():
    """Mock successful webhook response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'success': True}
    mock_response.text = 'OK'
    return mock_response


# ============================================================================
# Helper Functions
# ============================================================================

@pytest.fixture
def create_test_telemetry_data(db_cursor):
    """Helper to create test telemetry data"""
    def _create_data(device_id, metric_name, count=100):
        """Insert test telemetry records"""
        for i in range(count):
            db_cursor.execute("""
                INSERT INTO telemetry (device_id, metric_name, value, timestamp)
                VALUES (%s, %s, %s, NOW() - INTERVAL '%s minutes')
            """, (device_id, metric_name, 20.0 + i * 0.1, count - i))
        db_cursor.connection.commit()

    return _create_data


# ============================================================================
# Cleanup Hooks
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_logs():
    """Clean up test logs after each test"""
    yield
    # Add log cleanup logic if needed


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limits between tests"""
    yield
    # Add rate limit reset logic if needed

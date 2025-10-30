"""pytest configuration and shared fixtures"""
import pytest
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import uuid

# Set up test environment variables BEFORE importing any app code
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test_db'
os.environ['ERPNEXT_API_URL'] = 'http://localhost:8000'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only-do-not-use-in-production'
os.environ['TESTING'] = 'true'

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "crm voice"))
sys.path.insert(0, str(project_root / "core"))


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Setup cursor methods
    mock_cursor.fetchone = MagicMock(return_value=None)
    mock_cursor.fetchall = MagicMock(return_value=[])
    mock_cursor.execute = MagicMock()

    # Setup connection methods
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.execute = MagicMock(return_value=mock_cursor)
    mock_conn.commit = MagicMock()
    mock_conn.rollback = MagicMock()
    mock_conn.close = MagicMock()

    return mock_conn


@pytest.fixture
def mock_db_session(mock_db_connection):
    """Mock SQLAlchemy-style database session"""
    return mock_db_connection


@pytest.fixture
def sample_user():
    """Sample user data for testing"""
    return {
        'id': str(uuid.uuid4()),
        'email': 'test@insaautomation.com',
        'full_name': 'Test User',
        'password': 'TestPassword123!',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIrS.em9C2',  # Hash of "TestPassword123!"
        'role': 'sales_rep',
        'is_active': True,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'last_login': None
    }


@pytest.fixture
def sample_admin_user():
    """Sample admin user for testing"""
    return {
        'id': str(uuid.uuid4()),
        'email': 'admin@insaautomation.com',
        'full_name': 'Admin User',
        'password': 'AdminPass123!',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIrS.em9C2',
        'role': 'admin',
        'is_active': True,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'last_login': None
    }


@pytest.fixture
def sample_inactive_user():
    """Sample inactive user for testing"""
    return {
        'id': str(uuid.uuid4()),
        'email': 'inactive@insaautomation.com',
        'full_name': 'Inactive User',
        'password': 'InactivePass123!',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIrS.em9C2',
        'role': 'viewer',
        'is_active': False,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'last_login': None
    }


@pytest.fixture
def valid_jwt_token():
    """Sample valid JWT token payload"""
    return {
        'sub': str(uuid.uuid4()),
        'email': 'test@insaautomation.com',
        'role': 'sales_rep',
        'exp': datetime.utcnow() + timedelta(minutes=30)
    }


@pytest.fixture
def expired_jwt_token():
    """Sample expired JWT token payload"""
    return {
        'sub': str(uuid.uuid4()),
        'email': 'test@insaautomation.com',
        'role': 'sales_rep',
        'exp': datetime.utcnow() - timedelta(minutes=30)
    }


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    mock = Mock()
    mock.SECRET_KEY = "test-secret-key-for-jwt-signing-do-not-use-in-production"
    mock.ALGORITHM = "HS256"
    mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    return mock


@pytest.fixture
def flask_app():
    """Flask test client for crm-backend"""
    import os
    os.environ['TESTING'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///test.db'

    # Placeholder for now
    yield None


@pytest.fixture
def db_session():
    """Database session for testing"""
    # Placeholder for now
    yield None


@pytest.fixture
def mock_claude():
    """Mock Claude Code subprocess for testing"""
    mock = Mock()
    mock.query = MagicMock(return_value={
        'response': 'Test response',
        'agent': 'test_agent',
        'success': True
    })

    yield mock


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing"""
    return {
        'company': 'Test Oil & Gas Corp',
        'contact_name': 'John Doe',
        'email': 'john@testcorp.com',
        'industry': 'Oil & Gas',
        'description': 'Need pressure vessel for offshore platform'
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for authentication testing"""
    return {
        'email': 'test@insaautomation.com',
        'password': 'TestPassword123!',
        'full_name': 'Test User'
    }


@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Automatically cleanup test database after each test"""
    yield
    # TODO: Implement cleanup logic
    pass


@pytest.fixture
def authenticated_client(flask_app, sample_user_data):
    """Flask client with authenticated user"""
    # TODO: Implement authentication flow
    yield None


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

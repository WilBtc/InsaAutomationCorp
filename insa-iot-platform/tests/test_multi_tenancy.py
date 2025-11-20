"""
Comprehensive Multi-Tenancy Tests

This module tests:
- Tenant isolation (no cross-tenant data access)
- Quota enforcement
- Tenant CRUD operations
- User-tenant relationships
- Well assignments
- Row-Level Security (RLS)
- Super-admin privileges
"""

import pytest
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.auth import generate_token, hash_password, UserRole, TokenType
from app.services.tenant_service import TenantService
from app.services.quota_service import QuotaService
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    QuotaExceededError
)


class TestTenantService:
    """Test tenant service operations."""

    def test_create_tenant(self, db_pool):
        """Test creating a new tenant."""
        service = TenantService(db_pool)

        tenant = service.create_tenant(
            name="Test Tenant Alpha",
            plan="standard",
            metadata={"contact": "test@example.com"}
        )

        assert tenant['name'] == "Test Tenant Alpha"
        assert tenant['slug'] == "test-tenant-alpha"
        assert tenant['plan'] == "standard"
        assert tenant['status'] == "active"
        assert tenant['quotas'] is not None
        assert tenant['quotas']['api_calls_per_hour'] == 10000
        assert tenant['quotas']['max_wells'] == 50

    def test_create_tenant_duplicate_slug(self, db_pool):
        """Test that duplicate slugs are rejected."""
        service = TenantService(db_pool)

        # Create first tenant
        service.create_tenant(name="Test Tenant Beta", plan="standard")

        # Try to create duplicate
        with pytest.raises(ConflictError):
            service.create_tenant(name="Test Tenant Beta", plan="standard")

    def test_create_tenant_enterprise_quotas(self, db_pool):
        """Test enterprise tenant has higher quotas."""
        service = TenantService(db_pool)

        tenant = service.create_tenant(
            name="Enterprise Customer",
            plan="enterprise"
        )

        # Enterprise should have 10x standard quotas
        assert tenant['quotas']['api_calls_per_hour'] == 100000
        assert tenant['quotas']['max_wells'] == 500
        assert tenant['quotas']['features']['ml_predictions'] is True

    def test_get_tenant(self, db_pool, sample_tenant):
        """Test retrieving tenant by ID."""
        service = TenantService(db_pool)
        tenant = service.get_tenant(sample_tenant['id'])

        assert tenant['id'] == sample_tenant['id']
        assert tenant['name'] == sample_tenant['name']
        assert 'quotas' in tenant
        assert 'stats' in tenant

    def test_get_tenant_not_found(self, db_pool):
        """Test getting non-existent tenant."""
        service = TenantService(db_pool)

        with pytest.raises(NotFoundError):
            service.get_tenant(99999)

    def test_update_tenant(self, db_pool, sample_tenant):
        """Test updating tenant details."""
        service = TenantService(db_pool)

        updated = service.update_tenant(
            tenant_id=sample_tenant['id'],
            name="Updated Name",
            metadata={"updated": True}
        )

        assert updated['name'] == "Updated Name"
        assert updated['metadata']['updated'] is True

    def test_update_tenant_invalid_status(self, db_pool, sample_tenant):
        """Test that invalid status is rejected."""
        service = TenantService(db_pool)

        with pytest.raises(ValidationError):
            service.update_tenant(
                tenant_id=sample_tenant['id'],
                status="invalid_status"
            )

    def test_list_tenants(self, db_pool):
        """Test listing tenants with pagination."""
        service = TenantService(db_pool)

        # Create multiple tenants
        for i in range(5):
            service.create_tenant(
                name=f"List Test Tenant {i}",
                plan="standard"
            )

        tenants, total = service.list_tenants(limit=3, offset=0)

        assert len(tenants) <= 3
        assert total >= 5


class TestQuotaManagement:
    """Test quota enforcement."""

    def test_update_quotas(self, db_pool, sample_tenant):
        """Test updating tenant quotas."""
        service = TenantService(db_pool)

        updated = service.update_quota(
            tenant_id=sample_tenant['id'],
            api_calls_per_hour=20000,
            max_wells=100
        )

        assert updated['quotas']['api_calls_per_hour'] == 20000
        assert updated['quotas']['max_wells'] == 100

    def test_update_quotas_invalid_values(self, db_pool, sample_tenant):
        """Test that invalid quota values are rejected."""
        service = TenantService(db_pool)

        with pytest.raises(ValidationError):
            service.update_quota(
                tenant_id=sample_tenant['id'],
                api_calls_per_hour=-100  # Negative value
            )

    def test_check_and_increment_quota(self, db_pool, sample_tenant):
        """Test quota checking and incrementing."""
        quota_service = QuotaService(db_pool)

        # Should succeed initially
        allowed, info = quota_service.check_and_increment_api_quota(
            tenant_id=sample_tenant['id']
        )

        assert allowed is True
        assert info['hourly']['current'] > 0
        assert info['hourly']['limit'] > 0

    def test_quota_exceeded(self, db_pool, sample_tenant):
        """Test quota exceeded error."""
        # Update quotas to very low value
        tenant_service = TenantService(db_pool)
        tenant_service.update_quota(
            tenant_id=sample_tenant['id'],
            api_calls_per_hour=1
        )

        quota_service = QuotaService(db_pool)

        # First call should succeed
        allowed, _ = quota_service.check_and_increment_api_quota(
            tenant_id=sample_tenant['id']
        )
        assert allowed is True

        # Second call should fail
        with pytest.raises(QuotaExceededError) as exc_info:
            quota_service.check_and_increment_api_quota(
                tenant_id=sample_tenant['id']
            )

        assert exc_info.value.details['quota_type'] == 'hourly'

    def test_quota_status(self, db_pool, sample_tenant):
        """Test getting quota status."""
        quota_service = QuotaService(db_pool)

        # Make some API calls
        for _ in range(3):
            quota_service.check_and_increment_api_quota(
                tenant_id=sample_tenant['id']
            )

        status = quota_service.get_quota_status(sample_tenant['id'])

        assert status['hourly']['current'] >= 3
        assert status['hourly']['remaining'] > 0
        assert 'percent' in status['hourly']


class TestTenantIsolation:
    """Test tenant data isolation."""

    def test_tenant_cannot_access_other_tenant_data(self, db_pool, sample_tenant_a, sample_tenant_b):
        """Test that tenants cannot access each other's data."""
        # Set RLS context for tenant A
        db_pool.execute_query(
            "SET LOCAL app.current_tenant_id = %s",
            (sample_tenant_a['id'],),
            fetch=False
        )
        db_pool.execute_query(
            "SET LOCAL app.is_super_admin = 'false'",
            fetch=False
        )

        # Insert data for tenant A
        db_pool.execute_query(
            """
            INSERT INTO esp_telemetry (well_id, timestamp, flow_rate, pip, motor_current, tenant_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            ("WELL-A1", datetime.utcnow(), 1000.0, 150.0, 45.0, sample_tenant_a['id']),
            fetch=False
        )

        # Try to query as tenant B
        db_pool.execute_query(
            "SET LOCAL app.current_tenant_id = %s",
            (sample_tenant_b['id'],),
            fetch=False
        )

        result = db_pool.execute_query(
            "SELECT COUNT(*) FROM esp_telemetry WHERE well_id = 'WELL-A1'",
            fetch=True
        )

        # Tenant B should not see tenant A's data
        assert result[0][0] == 0

    def test_super_admin_can_access_all_data(self, db_pool, sample_tenant_a, sample_tenant_b):
        """Test that super-admins can access all tenant data."""
        # Insert data for both tenants
        for tenant, well_id in [(sample_tenant_a, 'WELL-A1'), (sample_tenant_b, 'WELL-B1')]:
            db_pool.execute_query(
                "SET LOCAL app.current_tenant_id = %s",
                (tenant['id'],),
                fetch=False
            )
            db_pool.execute_query(
                """
                INSERT INTO esp_telemetry (well_id, timestamp, flow_rate, pip, motor_current, tenant_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (well_id, datetime.utcnow(), 1000.0, 150.0, 45.0, tenant['id']),
                fetch=False
            )

        # Query as super-admin
        db_pool.execute_query(
            "SET LOCAL app.is_super_admin = 'true'",
            fetch=False
        )

        result = db_pool.execute_query(
            "SELECT COUNT(*) FROM esp_telemetry WHERE well_id IN ('WELL-A1', 'WELL-B1')",
            fetch=True
        )

        # Super-admin should see both
        assert result[0][0] == 2


class TestUserTenantRelationship:
    """Test user-tenant relationships."""

    def test_add_user_to_tenant(self, db_pool, sample_tenant, sample_user):
        """Test adding a user to a tenant."""
        service = TenantService(db_pool)

        relationship = service.add_user_to_tenant(
            tenant_id=sample_tenant['id'],
            user_id=sample_user['id'],
            role='operator',
            is_primary=False
        )

        assert relationship['tenant_id'] == sample_tenant['id']
        assert relationship['user_id'] == sample_user['id']
        assert relationship['role'] == 'operator'

    def test_add_user_exceeds_quota(self, db_pool, sample_tenant):
        """Test that adding users respects quota limits."""
        service = TenantService(db_pool)

        # Set low user quota
        service.update_quota(
            tenant_id=sample_tenant['id'],
            max_users=1
        )

        # Create and add first user (should succeed)
        user1_id = self._create_test_user(db_pool, "user1")
        service.add_user_to_tenant(
            tenant_id=sample_tenant['id'],
            user_id=user1_id,
            role='viewer'
        )

        # Try to add second user (should fail)
        user2_id = self._create_test_user(db_pool, "user2")
        with pytest.raises(ValidationError) as exc_info:
            service.add_user_to_tenant(
                tenant_id=sample_tenant['id'],
                user_id=user2_id,
                role='viewer'
            )

        assert 'quota' in exc_info.value.message.lower()

    def test_add_duplicate_user(self, db_pool, sample_tenant, sample_user):
        """Test that duplicate user-tenant relationships are rejected."""
        service = TenantService(db_pool)

        # Add user first time
        service.add_user_to_tenant(
            tenant_id=sample_tenant['id'],
            user_id=sample_user['id'],
            role='operator'
        )

        # Try to add same user again
        with pytest.raises(ConflictError):
            service.add_user_to_tenant(
                tenant_id=sample_tenant['id'],
                user_id=sample_user['id'],
                role='viewer'
            )

    def _create_test_user(self, db_pool, username: str) -> int:
        """Helper to create a test user."""
        result = db_pool.execute_query(
            """
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (username, hash_password("password123"), "viewer", datetime.utcnow()),
            fetch=True
        )
        return result[0][0]


class TestWellAssignment:
    """Test well-tenant assignments."""

    def test_assign_well_to_tenant(self, db_pool, sample_tenant):
        """Test assigning a well to a tenant."""
        service = TenantService(db_pool)

        assignment = service.assign_well_to_tenant(
            tenant_id=sample_tenant['id'],
            well_id="WELL-TEST-001",
            well_name="Test Well Alpha",
            location="North Field"
        )

        assert assignment['tenant_id'] == sample_tenant['id']
        assert assignment['well_id'] == "WELL-TEST-001"
        assert assignment['status'] == "active"

    def test_assign_well_exceeds_quota(self, db_pool, sample_tenant):
        """Test that well assignment respects quota limits."""
        service = TenantService(db_pool)

        # Set low well quota
        service.update_quota(
            tenant_id=sample_tenant['id'],
            max_wells=1
        )

        # Assign first well (should succeed)
        service.assign_well_to_tenant(
            tenant_id=sample_tenant['id'],
            well_id="WELL-001",
            well_name="Well 1"
        )

        # Try to assign second well (should fail)
        with pytest.raises(ValidationError) as exc_info:
            service.assign_well_to_tenant(
                tenant_id=sample_tenant['id'],
                well_id="WELL-002",
                well_name="Well 2"
            )

        assert 'quota' in exc_info.value.message.lower()

    def test_assign_duplicate_well(self, db_pool, sample_tenant):
        """Test that duplicate well assignments are rejected."""
        service = TenantService(db_pool)

        # Assign well first time
        service.assign_well_to_tenant(
            tenant_id=sample_tenant['id'],
            well_id="WELL-DUP-001",
            well_name="Duplicate Well"
        )

        # Try to assign same well again
        with pytest.raises(ConflictError):
            service.assign_well_to_tenant(
                tenant_id=sample_tenant['id'],
                well_id="WELL-DUP-001",
                well_name="Duplicate Well Again"
            )


class TestFeatureAccess:
    """Test feature access control."""

    def test_check_feature_access(self, db_pool, sample_tenant):
        """Test checking feature access."""
        service = TenantService(db_pool)

        # Standard plan should have basic features
        assert service.check_feature_access(sample_tenant['id'], 'advanced_analytics') is True
        assert service.check_feature_access(sample_tenant['id'], 'api_access') is True

    def test_feature_access_enterprise(self, db_pool):
        """Test enterprise features."""
        service = TenantService(db_pool)

        # Create enterprise tenant
        tenant = service.create_tenant(
            name="Enterprise Test",
            plan="enterprise"
        )

        # Enterprise should have all features
        assert service.check_feature_access(tenant['id'], 'ml_predictions') is True
        assert service.check_feature_access(tenant['id'], 'custom_reports') is True


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def db_pool():
    """Provide database connection pool for tests."""
    from app.db.pool import DatabasePool
    pool = DatabasePool()
    yield pool
    pool.close_all()


@pytest.fixture
def sample_tenant(db_pool):
    """Create a sample tenant for testing."""
    service = TenantService(db_pool)
    tenant = service.create_tenant(
        name=f"Test Tenant {datetime.utcnow().timestamp()}",
        plan="standard"
    )
    yield tenant
    # Cleanup handled by database cascade


@pytest.fixture
def sample_tenant_a(db_pool):
    """Create sample tenant A for isolation tests."""
    service = TenantService(db_pool)
    tenant = service.create_tenant(
        name=f"Tenant A {datetime.utcnow().timestamp()}",
        plan="standard"
    )
    yield tenant


@pytest.fixture
def sample_tenant_b(db_pool):
    """Create sample tenant B for isolation tests."""
    service = TenantService(db_pool)
    tenant = service.create_tenant(
        name=f"Tenant B {datetime.utcnow().timestamp()}",
        plan="standard"
    )
    yield tenant


@pytest.fixture
def sample_user(db_pool):
    """Create a sample user for testing."""
    result = db_pool.execute_query(
        """
        INSERT INTO users (username, password_hash, role, created_at)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (f"testuser_{datetime.utcnow().timestamp()}", hash_password("password123"), "operator", datetime.utcnow()),
        fetch=True
    )
    user_id = result[0][0]
    yield {"id": user_id}
    # Cleanup handled by database


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

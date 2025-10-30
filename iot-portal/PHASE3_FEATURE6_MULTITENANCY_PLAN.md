# Phase 3 Feature 6: Multi-tenancy - Implementation Plan

**Date**: October 28, 2025
**Status**: PLANNING
**Version**: INSA Advanced IIoT Platform v2.0
**Complexity**: HIGH - Requires schema changes, middleware, and extensive testing

## Table of Contents
1. [Overview](#overview)
2. [Multi-tenancy Architecture](#multi-tenancy-architecture)
3. [Database Schema Design](#database-schema-design)
4. [Middleware Implementation](#middleware-implementation)
5. [API Changes](#api-changes)
6. [Testing Strategy](#testing-strategy)
7. [Migration Plan](#migration-plan)
8. [Security Considerations](#security-considerations)
9. [Implementation Phases](#implementation-phases)

---

## Overview

### What is Multi-tenancy?

Multi-tenancy allows multiple organizations (tenants) to use the same INSA Advanced IIoT Platform instance while maintaining complete data isolation and tenant-specific customization.

### Business Value

**For INSA Automation Corp**:
- **SaaS Revenue Model**: Charge per tenant (monthly/annual subscriptions)
- **Operational Efficiency**: Single deployment serves hundreds of customers
- **Scalability**: Add new customers without new infrastructure
- **Cost Reduction**: Shared resources = lower per-customer cost

**For Customers**:
- **Lower Cost**: No dedicated infrastructure needed
- **Faster Onboarding**: Instant provisioning, no setup delays
- **Automatic Updates**: Always on latest version
- **Scalability**: Pay-as-you-grow pricing

### Use Cases

1. **Industrial Service Providers**: One INSA instance serving multiple factory clients
2. **OEM Equipment Monitoring**: Equipment manufacturers monitoring devices across customer sites
3. **System Integrator Platforms**: SIs managing projects for multiple end customers
4. **Enterprise Divisions**: Large corporations with separate business units

---

## Multi-tenancy Architecture

### Approach: Shared Database, Shared Schema

We'll use the **shared database, shared schema** approach with tenant discrimination via `tenant_id` column.

#### Why This Approach?

| Approach | Isolation | Cost | Scalability | Complexity |
|----------|-----------|------|-------------|------------|
| Separate Databases | ⭐⭐⭐⭐⭐ | 💰💰💰💰💰 | ⚠️ | HIGH |
| Separate Schemas | ⭐⭐⭐⭐ | 💰💰💰 | ⚙️ | MEDIUM |
| Shared Schema ✅ | ⭐⭐⭐ | 💰 | ✅ | LOW |

**Decision**: Shared schema is best for Phase 1 because:
- ✅ Existing PostgreSQL database can be extended
- ✅ Application-level isolation sufficient for IIoT use cases
- ✅ Cost-effective for 10-100 tenants
- ✅ Can migrate to separate DBs later if needed
- ✅ Simplest to implement and test

#### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  INSA Advanced IIoT Platform v2.0            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Flask Application (Port 5002)                │   │
│  │                                                       │   │
│  │  ┌────────────────────────────────────────────┐      │   │
│  │  │   Tenant Context Middleware               │      │   │
│  │  │   - Extracts tenant_id from JWT token     │      │   │
│  │  │   - Sets Flask g.tenant_id for request    │      │   │
│  │  │   - Validates tenant exists and is active │      │   │
│  │  └────────────────────────────────────────────┘      │   │
│  │                       ↓                               │   │
│  │  ┌────────────────────────────────────────────┐      │   │
│  │  │   Tenant-Aware API Endpoints              │      │   │
│  │  │   - All queries filtered by g.tenant_id   │      │   │
│  │  │   - Row-level security enforcement        │      │   │
│  │  └────────────────────────────────────────────┘      │   │
│  └──────────────────────────────────────────────────────┘   │
│                       ↓                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         PostgreSQL Database (insa_iiot)              │   │
│  │                                                       │   │
│  │  Tenant A Data  │  Tenant B Data  │  Tenant C Data   │   │
│  │  ─────────────  │  ─────────────  │  ─────────────   │   │
│  │  tenant_id=A    │  tenant_id=B    │  tenant_id=C     │   │
│  │  devices: 10    │  devices: 25    │  devices: 5      │   │
│  │  alerts: 100    │  alerts: 500    │  alerts: 50      │   │
│  │  users: 3       │  users: 8       │  users: 2        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Tenants Table**: Master table of all organizations
2. **Tenant Context Middleware**: Flask middleware to extract and validate tenant_id
3. **Tenant-Aware Models**: All models filtered by tenant_id
4. **Row-Level Security**: PostgreSQL RLS policies (optional hardening)
5. **Tenant Admin Panel**: Manage tenants, quotas, features

---

## Database Schema Design

### New Tables

#### 1. `tenants` Table

Master table storing all tenant organizations.

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,                   -- Organization name
    slug VARCHAR(100) NOT NULL UNIQUE,            -- URL-friendly identifier (e.g., 'acme-corp')
    domain VARCHAR(255),                          -- Custom domain (optional, e.g., 'acme.insa.cloud')

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, suspended, trial, churned
    tier VARCHAR(50) NOT  DEFAULT 'starter',      -- starter, professional, enterprise

    -- Branding
    logo_url TEXT,                                -- Tenant logo URL
    primary_color VARCHAR(7),                     -- Brand color (#FF5733)
    secondary_color VARCHAR(7),

    -- Quotas (NULL = unlimited)
    max_devices INTEGER,                          -- Device limit
    max_users INTEGER,                            -- User limit
    max_telemetry_points_per_day INTEGER,         -- Data ingestion limit
    max_retention_days INTEGER DEFAULT 90,        -- Data retention period

    -- Features (JSON for flexibility)
    enabled_features JSONB DEFAULT '{}',          -- {"ml": true, "advanced_alerting": false}

    -- Billing
    billing_email VARCHAR(255),
    billing_plan VARCHAR(50),                     -- monthly, annual
    billing_cycle_start DATE,
    billing_cycle_end DATE,
    mrr DECIMAL(10, 2),                           -- Monthly Recurring Revenue

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID,                              -- Admin user who created tenant
    metadata JSONB DEFAULT '{}'                   -- Custom metadata
);

-- Indexes
CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_created_at ON tenants(created_at);
```

#### 2. `tenant_users` Table (Join Table)

Maps users to tenants with role assignment.

```sql
CREATE TABLE tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id),   -- From existing RBAC

    -- Permissions
    is_tenant_admin BOOLEAN DEFAULT FALSE,        -- Can manage tenant settings

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, user_id)                    -- User can only be in tenant once
);

-- Indexes
CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_user ON tenant_users(user_id);
```

#### 3. `tenant_invitations` Table

Manage pending user invitations to tenants.

```sql
CREATE TABLE tenant_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role_id UUID NOT NULL REFERENCES roles(id),

    -- Invitation
    token VARCHAR(255) NOT NULL UNIQUE,           -- Secure invitation token
    invited_by UUID NOT NULL REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,                -- Expiration date
    accepted_at TIMESTAMP,                        -- NULL if pending
    accepted_by UUID REFERENCES users(id),        -- User who accepted

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CHECK (expires_at > created_at)
);

-- Indexes
CREATE INDEX idx_invitations_tenant ON tenant_invitations(tenant_id);
CREATE INDEX idx_invitations_email ON tenant_invitations(email);
CREATE INDEX idx_invitations_token ON tenant_invitations(token);
```

### Modified Tables

All existing tables need `tenant_id` column added:

```sql
-- Add tenant_id to all existing tables
ALTER TABLE devices ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE telemetry ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE rules ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE alerts ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE ml_models ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE anomaly_detections ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE retention_policies ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE escalation_policies ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE on_call_schedules ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Create indexes on tenant_id for performance
CREATE INDEX idx_devices_tenant ON devices(tenant_id);
CREATE INDEX idx_telemetry_tenant ON telemetry(tenant_id);
CREATE INDEX idx_rules_tenant ON rules(tenant_id);
CREATE INDEX idx_alerts_tenant ON alerts(tenant_id);
CREATE INDEX idx_ml_models_tenant ON ml_models(tenant_id);
CREATE INDEX idx_anomaly_detections_tenant ON anomaly_detections(tenant_id);
CREATE INDEX idx_retention_policies_tenant ON retention_policies(tenant_id);
CREATE INDEX idx_escalation_policies_tenant ON escalation_policies(tenant_id);
CREATE INDEX idx_on_call_schedules_tenant ON on_call_schedules(tenant_id);
```

### Row-Level Security (Optional)

PostgreSQL Row-Level Security (RLS) for defense-in-depth:

```sql
-- Enable RLS on all tenant-aware tables
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetry ENABLE ROW LEVEL SECURITY;
ALTER TABLE rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Create RLS policy (application sets tenant_id via SET LOCAL)
CREATE POLICY tenant_isolation_policy ON devices
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_policy ON telemetry
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_policy ON rules
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_policy ON alerts
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

---

## Middleware Implementation

### Tenant Context Middleware

Flask middleware to extract tenant context from JWT token and set `g.tenant_id`.

```python
#!/usr/bin/env python3
"""
Tenant Context Middleware
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 6

Extracts tenant_id from JWT token and enforces tenant isolation.
"""

from flask import g, request, jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class TenantContextMiddleware:
    """
    Middleware to extract and validate tenant context from JWT token.

    Sets g.tenant_id for all authenticated requests.
    """

    def __init__(self, app, db_config):
        self.app = app
        self.db_config = db_config

        # Endpoints that don't require tenant context
        self.exempt_paths = [
            '/health',
            '/api/v1/auth/login',
            '/api/v1/auth/register',
            '/api/v1/tenants/create',  # Superadmin only
            '/apidocs',
            '/apispec.json'
        ]

    def is_exempt(self, path):
        """Check if path is exempt from tenant context requirement."""
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
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(**self.db_config)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, slug, status, tier, enabled_features,
                           max_devices, max_users, max_telemetry_points_per_day
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

    def __call__(self, environ, start_response):
        """WSGI middleware entry point."""

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
            import psycopg2
            from psycopg2.extras import RealDictCursor

            # Get current count
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

                    # Additional quota types can be added here

            finally:
                conn.close()

            return f(*args, **kwargs)

        return decorated_function

    return decorator
```

---

## API Changes

### Modified Endpoints

All existing endpoints must be modified to filter by `tenant_id`:

#### Before (Single-tenant):
```python
@app.route('/api/v1/devices', methods=['GET'])
@require_auth
def list_devices():
    cursor.execute("SELECT * FROM devices ORDER BY created_at DESC")
    devices = cursor.fetchall()
    return jsonify({'devices': devices})
```

#### After (Multi-tenant):
```python
@app.route('/api/v1/devices', methods=['GET'])
@require_auth
@require_tenant  # New decorator
def list_devices():
    tenant_id = g.tenant_id  # From middleware
    cursor.execute(
        "SELECT * FROM devices WHERE tenant_id = %s ORDER BY created_at DESC",
        (tenant_id,)
    )
    devices = cursor.fetchall()
    return jsonify({'devices': devices})
```

### New Endpoints

#### Tenant Management API

```python
# GET /api/v1/tenants - List all tenants (superadmin only)
# POST /api/v1/tenants - Create new tenant (superadmin only)
# GET /api/v1/tenants/{id} - Get tenant details
# PATCH /api/v1/tenants/{id} - Update tenant
# DELETE /api/v1/tenants/{id} - Delete tenant (superadmin only)
```

#### Tenant User Management API

```python
# GET /api/v1/tenants/{id}/users - List tenant users
# POST /api/v1/tenants/{id}/users/invite - Invite user to tenant
# DELETE /api/v1/tenants/{id}/users/{user_id} - Remove user from tenant
# PATCH /api/v1/tenants/{id}/users/{user_id}/role - Change user role
```

#### Tenant Quota API

```python
# GET /api/v1/tenants/{id}/quotas - Get current quota usage
# PATCH /api/v1/tenants/{id}/quotas - Update quota limits (superadmin)
```

---

## Testing Strategy

### Unit Tests

1. **Middleware Tests**: Tenant context extraction, validation
2. **Model Tests**: Tenant filtering, quota enforcement
3. **API Tests**: Tenant isolation, unauthorized access

### Integration Tests

1. **Multi-Tenant Isolation**: Verify Tenant A cannot see Tenant B's data
2. **Quota Enforcement**: Test quota limits work correctly
3. **User Management**: Invite, accept, remove users
4. **Tenant CRUD**: Create, read, update, delete tenants

### Test Scenarios

```python
def test_tenant_isolation():
    """Verify Tenant A cannot access Tenant B's devices."""

    # Create 2 tenants
    tenant_a = create_tenant("Acme Corp")
    tenant_b = create_tenant("Beta Industries")

    # Create devices for each tenant
    device_a = create_device(tenant_a.id, "Device A")
    device_b = create_device(tenant_b.id, "Device B")

    # Login as Tenant A user
    token_a = login_user(tenant_a_user)

    # Try to access all devices
    response = client.get('/api/v1/devices', headers={'Authorization': f'Bearer {token_a}'})

    # Should only see Tenant A's device
    assert len(response.json['devices']) == 1
    assert response.json['devices'][0]['id'] == device_a.id
    assert device_b.id not in [d['id'] for d in response.json['devices']]


def test_device_quota_enforcement():
    """Verify device quota is enforced."""

    # Create tenant with max_devices=2
    tenant = create_tenant("Limited Corp", max_devices=2)

    # Create 2 devices (at limit)
    device1 = create_device(tenant.id, "Device 1")
    device2 = create_device(tenant.id, "Device 2")

    # Try to create 3rd device
    token = login_user(tenant_user)
    response = client.post('/api/v1/devices',
                           json={'name': 'Device 3'},
                           headers={'Authorization': f'Bearer {token}'})

    # Should fail with HTTP 429
    assert response.status_code == 429
    assert 'quota exceeded' in response.json['error']
```

---

## Migration Plan

### Phase 1: Schema Migration (Week 1)

1. **Create new tables**: tenants, tenant_users, tenant_invitations
2. **Add tenant_id columns** to existing tables
3. **Create indexes** on tenant_id columns
4. **Create default tenant**: Migrate existing data to "INSA Default" tenant

```sql
-- Migration script
BEGIN;

-- 1. Create new tables (see schema above)
-- 2. Create default tenant
INSERT INTO tenants (name, slug, status, tier)
VALUES ('INSA Default', 'default', 'active', 'enterprise')
RETURNING id INTO default_tenant_id;

-- 3. Update existing data with default tenant
UPDATE devices SET tenant_id = default_tenant_id;
UPDATE telemetry SET tenant_id = default_tenant_id;
UPDATE rules SET tenant_id = default_tenant_id;
UPDATE alerts SET tenant_id = default_tenant_id;
UPDATE ml_models SET tenant_id = default_tenant_id;

-- 4. Make tenant_id NOT NULL after migration
ALTER TABLE devices ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE telemetry ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE rules ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE alerts ALTER COLUMN tenant_id SET NOT NULL;

COMMIT;
```

### Phase 2: Application Migration (Week 2)

1. **Implement middleware**: TenantContextMiddleware
2. **Update all queries**: Add `WHERE tenant_id = %s` filters
3. **Add decorators**: @require_tenant on all endpoints
4. **Implement tenant APIs**: CRUD operations for tenants

### Phase 3: Testing & Validation (Week 3)

1. **Write tests**: 50+ tests for tenant isolation
2. **Manual testing**: Create multiple tenants, verify isolation
3. **Performance testing**: Query performance with tenant_id filters
4. **Security audit**: Verify no data leaks between tenants

---

## Security Considerations

### Data Isolation

1. **Application-Level Filtering**: All queries MUST include `WHERE tenant_id = %s`
2. **Middleware Enforcement**: Tenant context set on every request
3. **Row-Level Security**: PostgreSQL RLS as defense-in-depth
4. **API Testing**: Automated tests verify no cross-tenant access

### Authentication & Authorization

1. **JWT Tokens**: Include `tenant_id` claim in token
2. **Token Validation**: Verify tenant is active before allowing access
3. **Role-Based Access**: Existing RBAC system works within tenant context
4. **Tenant Admins**: Special permission to manage tenant users/settings

### Quota Enforcement

1. **Hard Limits**: Prevent resource exhaustion
2. **Soft Limits**: Warn when approaching quota
3. **Graceful Degradation**: Return HTTP 429 with clear error message
4. **Billing Integration**: Automatically upgrade tier when quota exceeded

---

## Implementation Phases

### Phase 1: Core Multi-tenancy (1 week)

**Deliverables**:
- ✅ Database schema with tenants table
- ✅ Tenant context middleware
- ✅ Modified queries with tenant_id filtering
- ✅ Basic tenant CRUD API

**Success Criteria**:
- Can create multiple tenants
- Each tenant sees only their own data
- No cross-tenant data leaks in tests

### Phase 2: Tenant Management (1 week)

**Deliverables**:
- ✅ User invitation system
- ✅ Tenant admin panel
- ✅ Quota enforcement
- ✅ Tenant settings API

**Success Criteria**:
- Can invite users to tenants
- Quotas enforced correctly
- Tenant admins can manage users

### Phase 3: Advanced Features (1 week)

**Deliverables**:
- ✅ Custom branding (logo, colors)
- ✅ Feature flags per tenant
- ✅ Billing integration hooks
- ✅ Tenant analytics dashboard

**Success Criteria**:
- Tenants can customize branding
- Feature flags work correctly
- Billing data tracked accurately

---

## Next Steps

1. **Review Plan**: Get approval on architecture approach
2. **Create Migration Script**: Write SQL migration for schema changes
3. **Implement Middleware**: Build TenantContextMiddleware
4. **Update Queries**: Modify all database queries to include tenant_id
5. **Write Tests**: Create comprehensive test suite
6. **Deploy to Production**: Phased rollout with monitoring

---

**Estimated Total Effort**: 3 weeks (120 hours)
- Database Migration: 20 hours
- Middleware & Core Logic: 40 hours
- API Endpoints: 30 hours
- Testing: 20 hours
- Documentation: 10 hours

**Risk Level**: MEDIUM-HIGH
- Requires careful testing to prevent data leaks
- Schema changes affect all existing data
- Performance impact of tenant_id filters

**Recommendation**: Implement in development environment first, extensive testing before production

---

*Document Date: October 28, 2025*
*Author: INSA Automation Corp*
*Platform: INSA Advanced IIoT Platform v2.0*

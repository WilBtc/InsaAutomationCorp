# Phase 3 Feature 6: Multi-tenancy Integration Plan

**Date**: October 28, 2025
**Status**: IN PROGRESS
**Version**: INSA Advanced IIoT Platform v2.0

## Completion Status

✅ **Completed**:
1. Database migration (001_add_multitenancy.sql) - 500+ lines
2. Tenant management module (tenant_manager.py) - 850+ lines
3. Tenant middleware (tenant_middleware.py) - 470+ lines

🔄 **In Progress**:
4. Application integration (app_advanced.py modifications)

## Required Changes to app_advanced.py

### 1. Add Imports (Top of File)

```python
from flask import Flask, request, jsonify, g
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
```

### 2. Store DB_CONFIG in app.config

Add after line 168:

```python
# Store DB_CONFIG in app for middleware access
app.config['DB_CONFIG'] = DB_CONFIG
```

### 3. Initialize Tenant Middleware (Before app.run())

Add in `if __name__ == '__main__':` section:

```python
# Initialize tenant context middleware
logger.info("Initializing tenant context middleware...")
app.wsgi_app = TenantContextMiddleware(app.wsgi_app, DB_CONFIG)
logger.info("✅ Tenant context middleware initialized")
```

### 4. Modify Login Endpoint (Line 658)

**Current** (lines 674-691):
```python
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
```

**New** (with tenant_id):
```python
cur.execute("""
    SELECT id, email, password_hash, role, permissions
    FROM users
    WHERE email = %s
""", (data['email'],))

user = cur.fetchone()

if not user or not verify_password(data['password'], user['password_hash']):
    return jsonify({'error': 'Invalid credentials'}), 401

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
```

### 5. Create require_auth Decorator

Add after database utility functions (around line 280):

```python
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
        from flask_jwt_extended import get_jwt

        # Get full JWT claims
        claims = get_jwt()

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
```

### 6. Update Device Endpoints (Lines 760-900)

**Before**:
```python
@app.route('/api/v1/devices', methods=['GET'])
@jwt_required()
def list_devices():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM devices ORDER BY created_at DESC")
        devices = cur.fetchall()
        return jsonify({'devices': devices})
```

**After**:
```python
@app.route('/api/v1/devices', methods=['GET'])
@require_auth
@require_tenant
def list_devices():
    """List devices for current tenant"""
    tenant_id = g.tenant_id

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM devices
            WHERE tenant_id = %s
            ORDER BY created_at DESC
        """, (tenant_id,))
        devices = cur.fetchall()
        return jsonify({'devices': devices})
```

### 7. Update CREATE Device Endpoint

**Before**:
```python
@app.route('/api/v1/devices', methods=['POST'])
@jwt_required()
def create_device():
    data = request.get_json()
    # ... validation ...

    cur.execute("""
        INSERT INTO devices (id, name, type, protocol, status, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *
    """, (device_id, name, device_type, protocol, 'active', json.dumps(metadata)))
```

**After**:
```python
@app.route('/api/v1/devices', methods=['POST'])
@require_auth
@require_tenant
@check_tenant_quota('devices')  # Check quota before creating
def create_device():
    """Create new device for current tenant"""
    tenant_id = g.tenant_id
    data = request.get_json()
    # ... validation ...

    cur.execute("""
        INSERT INTO devices (id, name, type, protocol, status, tenant_id, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """, (device_id, name, device_type, protocol, 'active', tenant_id, json.dumps(metadata)))
```

### 8. Tables Requiring tenant_id Filtering

All queries to these tables must include `WHERE tenant_id = %s`:

1. **devices** - All CRUD operations
2. **telemetry** - Data ingestion and queries
3. **rules** - Rule management
4. **alerts** - Alert queries
5. **api_keys** - API key management
6. **ml_models** - ML models (if Feature 2 enabled)
7. **anomaly_detections** - Anomalies (if Feature 2 enabled)
8. **retention_policies** - Retention (if Feature 7 enabled)
9. **archived_data_index** - Archived data (if Feature 7 enabled)
10. **escalation_policies** - Escalations (if Feature 8 enabled)
11. **on_call_schedules** - On-call (if Feature 8 enabled)
12. **alert_states** - Alert tracking (if Feature 8 enabled)

### 9. New API Endpoints to Add

#### Tenant Management API

```python
@app.route('/api/v1/tenants', methods=['GET'])
@require_auth
def list_all_tenants():
    """List all tenants (superadmin only)"""
    # Check if user has superadmin role
    if g.current_user.get('role') != 'superadmin':
        return jsonify({'error': 'Superadmin required'}), 403

    with TenantManager(DB_CONFIG) as manager:
        tenants = manager.list_tenants()
        return jsonify({'tenants': tenants})


@app.route('/api/v1/tenants', methods=['POST'])
@require_auth
def create_tenant():
    """Create new tenant (superadmin only)"""
    if g.current_user.get('role') != 'superadmin':
        return jsonify({'error': 'Superadmin required'}), 403

    data = request.get_json()

    with TenantManager(DB_CONFIG) as manager:
        tenant = manager.create_tenant(
            name=data['name'],
            slug=data['slug'],
            tier=data.get('tier', 'starter'),
            max_devices=data.get('max_devices'),
            max_users=data.get('max_users'),
            created_by=g.current_user['id']
        )
        return jsonify({'tenant': tenant}), 201


@app.route('/api/v1/tenants/<tenant_id>', methods=['GET'])
@require_auth
@require_tenant
def get_tenant(tenant_id):
    """Get tenant details (own tenant or superadmin)"""
    if g.tenant_id != tenant_id and g.current_user.get('role') != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403

    with TenantManager(DB_CONFIG) as manager:
        tenant = manager.get_tenant(tenant_id)
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        return jsonify({'tenant': tenant})


@app.route('/api/v1/tenants/<tenant_id>', methods=['PATCH'])
@require_auth
@require_tenant
@require_tenant_admin
def update_tenant(tenant_id):
    """Update tenant (tenant admin only)"""
    if g.tenant_id != tenant_id:
        return jsonify({'error': 'Can only update own tenant'}), 403

    data = request.get_json()

    with TenantManager(DB_CONFIG) as manager:
        tenant = manager.update_tenant(tenant_id, **data)
        return jsonify({'tenant': tenant})


@app.route('/api/v1/tenants/<tenant_id>/stats', methods=['GET'])
@require_auth
@require_tenant
def get_tenant_stats(tenant_id):
    """Get tenant statistics"""
    if g.tenant_id != tenant_id and g.current_user.get('role') != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403

    with TenantManager(DB_CONFIG) as manager:
        stats = manager.get_tenant_stats(tenant_id)
        return jsonify({'stats': stats})


@app.route('/api/v1/tenants/<tenant_id>/users', methods=['GET'])
@require_auth
@require_tenant
@require_tenant_admin
def list_tenant_users(tenant_id):
    """List users in tenant (tenant admin only)"""
    if g.tenant_id != tenant_id:
        return jsonify({'error': 'Unauthorized'}), 403

    with TenantManager(DB_CONFIG) as manager:
        users = manager.list_tenant_users(tenant_id)
        return jsonify({'users': users})


@app.route('/api/v1/tenants/<tenant_id>/users/invite', methods=['POST'])
@require_auth
@require_tenant
@require_tenant_admin
@check_tenant_quota('users')
def invite_user_to_tenant(tenant_id):
    """Invite user to tenant (tenant admin only)"""
    if g.tenant_id != tenant_id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    with TenantManager(DB_CONFIG) as manager:
        invitation = manager.create_invitation(
            tenant_id=tenant_id,
            email=data['email'],
            role_id=data['role_id'],
            invited_by=g.current_user['id']
        )

        # TODO: Send invitation email

        return jsonify({'invitation': invitation}), 201


@app.route('/api/v1/tenants/<tenant_id>/users/<user_id>', methods=['DELETE'])
@require_auth
@require_tenant
@require_tenant_admin
def remove_user_from_tenant(tenant_id, user_id):
    """Remove user from tenant (tenant admin only)"""
    if g.tenant_id != tenant_id:
        return jsonify({'error': 'Unauthorized'}), 403

    with TenantManager(DB_CONFIG) as manager:
        success = manager.remove_user_from_tenant(tenant_id, user_id)
        if not success:
            return jsonify({'error': 'User not found in tenant'}), 404
        return jsonify({'success': True})


@app.route('/api/v1/tenants/<tenant_id>/quotas', methods=['GET'])
@require_auth
@require_tenant
def get_tenant_quotas(tenant_id):
    """Get tenant quota usage"""
    if g.tenant_id != tenant_id and g.current_user.get('role') != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403

    with TenantManager(DB_CONFIG) as manager:
        device_quota = manager.check_device_quota(tenant_id)
        user_quota = manager.check_user_quota(tenant_id)

        return jsonify({
            'quotas': {
                'devices': device_quota,
                'users': user_quota
            }
        })
```

## Implementation Checklist

### Phase 1: Core Integration (Week 1)
- [ ] Add imports for tenant modules
- [ ] Store DB_CONFIG in app.config
- [ ] Initialize tenant middleware
- [ ] Create require_auth decorator
- [ ] Modify login endpoint to include tenant_id in JWT
- [ ] Test authentication with tenant context

### Phase 2: Endpoint Updates (Week 2)
- [ ] Update devices endpoints (GET, POST, PATCH, DELETE)
- [ ] Update telemetry endpoints
- [ ] Update rules endpoints
- [ ] Update alerts endpoints
- [ ] Update api_keys endpoints
- [ ] Add tenant management endpoints (10 new endpoints)

### Phase 3: Feature Integration (Week 3)
- [ ] Update ML API endpoints (if Feature 2 enabled)
- [ ] Update Retention API endpoints (Feature 7)
- [ ] Update Alerting API endpoints (Feature 8)
- [ ] Add quota enforcement decorators
- [ ] Add feature flag checks

### Phase 4: Testing (Week 4)
- [ ] Create test script for tenant isolation
- [ ] Test quota enforcement
- [ ] Test multi-tenant scenarios
- [ ] Performance testing with tenant_id indexes
- [ ] Security audit (cross-tenant access attempts)

## Migration Strategy

### Step 1: Deploy Database Migration
```bash
PGPASSWORD=iiot_secure_2025 psql -h localhost -U iiot_user -d insa_iiot \
  -f migrations/001_add_multitenancy.sql
```

### Step 2: Update Application Code
- Apply all changes from this document to app_advanced.py
- Total estimated changes: 300-500 lines of code

### Step 3: Test Authentication
```bash
# Login and get JWT with tenant_id
curl -X POST http://localhost:5002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@insa.com","password":"Admin123!"}'

# Decode JWT to verify tenant_id claim is present
```

### Step 4: Test Tenant Isolation
```bash
# Create second tenant
curl -X POST http://localhost:5002/api/v1/tenants \
  -H "Authorization: Bearer {superadmin_token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Corp","slug":"test-corp","tier":"starter","max_devices":10}'

# Verify Tenant A cannot see Tenant B's devices
```

## Success Criteria

✅ **Authentication**:
- JWT tokens include tenant_id claim
- Login fails if user has no active tenant
- Tokens can be decoded and validated

✅ **Tenant Isolation**:
- Queries filtered by tenant_id
- No cross-tenant data leaks
- Unauthorized access returns HTTP 403

✅ **Quota Enforcement**:
- Device quota prevents creation when limit reached
- User quota prevents invitations when limit reached
- Returns HTTP 429 with clear error message

✅ **Performance**:
- Query performance with tenant_id indexes acceptable (<100ms avg)
- No N+1 query issues

## Rollback Plan

If issues occur:

1. **Database**: Migration is transactional - already committed, would require reverse migration
2. **Application**: Revert app_advanced.py changes and restart
3. **Data**: All existing data migrated to default tenant - no data loss

---

**Next Steps**: Apply changes from Section "Required Changes to app_advanced.py"

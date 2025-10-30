# Multi-Tenancy Phase 3 - Tenant Management API Implementation Plan

**Date**: October 29, 2025 03:30 UTC
**Status**: 📋 PLANNING COMPLETE - Ready to implement
**Version**: INSA Advanced IIoT Platform v2.0
**Duration**: 1-2 days estimated

---

## 🎯 OBJECTIVE

Implement 10 tenant management API endpoints to expose all tenant management functionality from `tenant_manager.py` via REST API.

**Goal**: Enable programmatic tenant administration through API (CRUD operations, user management, quota monitoring)

---

## ✅ PREREQUISITES (COMPLETE)

- ✅ Phase 1: Database schema with tenant tables
- ✅ Phase 2: All 23 endpoints secured with tenant filtering
- ✅ Tenant manager: `tenant_manager.py` (735 lines, all CRUD methods)
- ✅ Tenant middleware: `tenant_middleware.py` (493 lines, all decorators)
- ✅ JWT authentication with tenant context

---

## 📋 PHASE 3 DELIVERABLES

### 10 Tenant Management Endpoints

| # | Endpoint | Method | Purpose | Auth | Lines |
|---|----------|--------|---------|------|-------|
| 1 | `/api/v1/tenants` | GET | List all tenants | Admin only | ~80 |
| 2 | `/api/v1/tenants` | POST | Create new tenant | Admin only | ~100 |
| 3 | `/api/v1/tenants/:id` | GET | Get tenant details | Tenant member | ~60 |
| 4 | `/api/v1/tenants/:id` | PATCH | Update tenant settings | Tenant admin | ~80 |
| 5 | `/api/v1/tenants/:id/stats` | GET | Get tenant statistics | Tenant member | ~60 |
| 6 | `/api/v1/tenants/:id/users` | GET | List tenant users | Tenant member | ~60 |
| 7 | `/api/v1/tenants/:id/users/invite` | POST | Invite user to tenant | Tenant admin | ~100 |
| 8 | `/api/v1/tenants/:id/users/:user_id` | DELETE | Remove user from tenant | Tenant admin | ~70 |
| 9 | `/api/v1/tenants/:id/users/:user_id/role` | PATCH | Update user role | Tenant admin | ~80 |
| 10 | `/api/v1/tenants/:id/quotas` | GET | Get quota usage | Tenant member | ~50 |

**Total Estimated Lines**: ~740 lines of code

---

## 🏗️ DETAILED IMPLEMENTATION

### Endpoint 1: List All Tenants (Admin Only)

```python
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
        200: {
            "tenants": [
                {
                    "id": "uuid",
                    "name": "INSA Automation Corp",
                    "slug": "insa-default",
                    "tier": "enterprise",
                    "max_devices": null,
                    "max_users": null,
                    "created_at": "2025-10-28T12:00:00Z"
                }
            ],
            "total": 1,
            "page": 1,
            "limit": 50
        }
        403: Not system admin
    """
    # Get current user
    user_id = get_jwt_identity()

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
```

**Test Commands**:
```bash
# Get JWT token
TOKEN=$(curl -X POST http://localhost:5002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@insa.com","password":"Admin123!"}' | jq -r .access_token)

# List all tenants
curl http://localhost:5002/api/v1/tenants \
  -H "Authorization: Bearer $TOKEN"

# Filter by tier
curl "http://localhost:5002/api/v1/tenants?tier=enterprise" \
  -H "Authorization: Bearer $TOKEN"

# Search
curl "http://localhost:5002/api/v1/tenants?search=INSA" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Endpoint 2: Create New Tenant (Admin Only)

```python
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
            "max_users": 10,
            "max_storage_mb": 5000
        }

    Returns:
        201: {
            "id": "uuid",
            "name": "Acme Corp",
            "slug": "acme-corp",
            "tier": "professional",
            "created_at": "2025-10-29T03:00:00Z"
        }
        403: Not system admin
        400: Validation error (slug exists, invalid tier)
    """
    # Check system admin
    user_id = get_jwt_identity()
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

    # Validate tier
    valid_tiers = ['free', 'startup', 'professional', 'enterprise']
    if data['tier'] not in valid_tiers:
        return jsonify({'error': 'Invalid tier'}), 400

    # Use tenant_manager to create tenant
    from tenant_manager import TenantManager

    try:
        with TenantManager(DB_CONFIG) as manager:
            tenant_id = manager.create_tenant(
                name=data['name'],
                slug=data['slug'],
                tier=data['tier'],
                max_devices=data.get('max_devices'),
                max_users=data.get('max_users'),
                max_storage_mb=data.get('max_storage_mb')
            )

            # Get created tenant
            tenant = manager.get_tenant(tenant_id)

        return jsonify(tenant), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        return jsonify({'error': 'Failed to create tenant'}), 500
```

**Test Commands**:
```bash
# Create new tenant
curl -X POST http://localhost:5002/api/v1/tenants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "slug": "test-company",
    "tier": "professional",
    "max_devices": 50,
    "max_users": 5
  }'

# Expected: 201 with tenant object
```

---

### Endpoint 3: Get Tenant Details

```python
@app.route('/api/v1/tenants/<tenant_id>', methods=['GET'])
@require_auth
@require_tenant
def get_tenant(tenant_id):
    """
    Get tenant details (must be member of tenant or system admin)

    Returns:
        200: {
            "id": "uuid",
            "name": "INSA Automation Corp",
            "slug": "insa-default",
            "tier": "enterprise",
            "max_devices": null,
            "max_users": null,
            "created_at": "2025-10-28T12:00:00Z"
        }
        403: Not authorized
        404: Tenant not found
    """
    # Check access
    user_id = get_jwt_identity()
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
```

**Test Commands**:
```bash
# Get tenant details (your own tenant)
curl http://localhost:5002/api/v1/tenants/{tenant_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

### Endpoint 4: Update Tenant Settings

```python
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

    from tenant_manager import TenantManager

    try:
        with TenantManager(DB_CONFIG) as manager:
            manager.update_tenant(
                tenant_id=tenant_id,
                name=data.get('name'),
                tier=data.get('tier'),
                max_devices=data.get('max_devices'),
                max_users=data.get('max_users'),
                max_storage_mb=data.get('max_storage_mb')
            )

            # Get updated tenant
            tenant = manager.get_tenant(tenant_id)

        return jsonify(tenant), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to update tenant: {e}")
        return jsonify({'error': 'Failed to update tenant'}), 500
```

---

### Endpoint 5: Get Tenant Statistics

```python
@app.route('/api/v1/tenants/<tenant_id>/stats', methods=['GET'])
@require_auth
@require_tenant
def get_tenant_stats(tenant_id):
    """
    Get tenant statistics (usage counts)

    Returns:
        200: {
            "device_count": 3,
            "user_count": 2,
            "rule_count": 9,
            "alert_count": 11,
            "telemetry_count": 103,
            "storage_used_mb": 2.5
        }
        403: Not authorized
    """
    # Check access (same as get_tenant)
    user_id = get_jwt_identity()
    user_tenant_id = g.tenant_id

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    is_admin = user and user['is_admin']

    if not is_admin and str(user_tenant_id) != tenant_id:
        return jsonify({'error': 'Access denied'}), 403

    # Get stats using tenant_manager
    from tenant_manager import TenantManager

    try:
        with TenantManager(DB_CONFIG) as manager:
            stats = manager.get_tenant_stats(tenant_id)

        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Failed to get tenant stats: {e}")
        return jsonify({'error': 'Failed to get tenant stats'}), 500
```

**Test Commands**:
```bash
# Get tenant statistics
curl http://localhost:5002/api/v1/tenants/{tenant_id}/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

### Endpoint 6: List Tenant Users

```python
@app.route('/api/v1/tenants/<tenant_id>/users', methods=['GET'])
@require_auth
@require_tenant
def list_tenant_users(tenant_id):
    """
    List all users in tenant

    Returns:
        200: {
            "users": [
                {
                    "user_id": "uuid",
                    "email": "user@example.com",
                    "role": "member",
                    "is_tenant_admin": false,
                    "joined_at": "2025-10-28T12:00:00Z"
                }
            ]
        }
        403: Not authorized
    """
    # Check access
    user_id = get_jwt_identity()
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
        SELECT tu.user_id, u.email, tu.role, tu.is_tenant_admin, tu.joined_at
        FROM tenant_users tu
        JOIN users u ON tu.user_id = u.id
        WHERE tu.tenant_id = %s
        ORDER BY tu.joined_at DESC
    """, (tenant_id,))
    users = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({'users': [dict(u) for u in users]}), 200
```

---

### Endpoint 7: Invite User to Tenant

```python
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
        201: {
            "invitation_id": "uuid",
            "email": "newuser@example.com",
            "token": "random_token",
            "expires_at": "2025-11-05T03:00:00Z"
        }
        400: Validation error (user already member, invalid role)
    """
    data = request.get_json()

    if not data.get('email'):
        return jsonify({'error': 'Email required'}), 400

    # Use tenant_manager to create invitation
    from tenant_manager import TenantManager

    try:
        with TenantManager(DB_CONFIG) as manager:
            invitation = manager.invite_user(
                tenant_id=tenant_id,
                email=data['email'],
                role=data.get('role', 'member'),
                invited_by=get_jwt_identity()
            )

        # TODO: Send invitation email

        return jsonify(invitation), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to invite user: {e}")
        return jsonify({'error': 'Failed to invite user'}), 500
```

**Test Commands**:
```bash
# Invite user
curl -X POST http://localhost:5002/api/v1/tenants/{tenant_id}/users/invite \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "role": "member"
  }'
```

---

### Endpoint 8: Remove User from Tenant

```python
@app.route('/api/v1/tenants/<tenant_id>/users/<user_id>', methods=['DELETE'])
@require_auth
@require_tenant_admin
def remove_user_from_tenant(tenant_id, user_id):
    """
    Remove user from tenant (tenant admin only)

    Returns:
        204: User removed
        400: Cannot remove (last admin, trying to remove self)
        404: User not found in tenant
    """
    # Use tenant_manager
    from tenant_manager import TenantManager

    try:
        with TenantManager(DB_CONFIG) as manager:
            manager.remove_user(tenant_id, user_id)

        return '', 204

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to remove user: {e}")
        return jsonify({'error': 'Failed to remove user'}), 500
```

**Test Commands**:
```bash
# Remove user
curl -X DELETE http://localhost:5002/api/v1/tenants/{tenant_id}/users/{user_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

### Endpoint 9: Update User Role

```python
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
        404: User not found in tenant
    """
    data = request.get_json()

    # Use tenant_manager
    from tenant_manager import TenantManager

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
```

**Test Commands**:
```bash
# Update user role
curl -X PATCH http://localhost:5002/api/v1/tenants/{tenant_id}/users/{user_id}/role \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin",
    "is_tenant_admin": true
  }'
```

---

### Endpoint 10: Get Quota Usage

```python
@app.route('/api/v1/tenants/<tenant_id>/quotas', methods=['GET'])
@require_auth
@require_tenant
def get_tenant_quotas(tenant_id):
    """
    Get tenant quota usage

    Returns:
        200: {
            "devices": {
                "used": 3,
                "limit": null,
                "percentage": null
            },
            "users": {
                "used": 2,
                "limit": null,
                "percentage": null
            },
            "storage": {
                "used_mb": 2.5,
                "limit_mb": null,
                "percentage": null
            }
        }
        403: Not authorized
    """
    # Check access
    user_id = get_jwt_identity()
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
        SELECT max_devices, max_users, max_storage_mb
        FROM tenants
        WHERE id = %s
    """, (tenant_id,))
    tenant = cur.fetchone()

    # Get usage stats
    from tenant_manager import TenantManager

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
            'storage': {
                'used_mb': stats['storage_used_mb'],
                'limit_mb': tenant['max_storage_mb'],
                'percentage': (stats['storage_used_mb'] / tenant['max_storage_mb'] * 100) if tenant['max_storage_mb'] else None
            }
        }

        return jsonify(quotas), 200

    except Exception as e:
        logger.error(f"Failed to get quotas: {e}")
        return jsonify({'error': 'Failed to get quotas'}), 500
```

**Test Commands**:
```bash
# Get quota usage
curl http://localhost:5002/api/v1/tenants/{tenant_id}/quotas \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Step 1: Add Imports (10 minutes)
```python
# Add to top of app_advanced.py
from tenant_manager import TenantManager
from tenant_middleware import require_tenant_admin
```

### Step 2: Implement Endpoints (4-6 hours)
- ✅ Endpoint 1: List tenants (1 hour)
- ✅ Endpoint 2: Create tenant (1 hour)
- ✅ Endpoint 3: Get tenant (30 min)
- ✅ Endpoint 4: Update tenant (30 min)
- ✅ Endpoint 5: Get stats (30 min)
- ✅ Endpoint 6: List users (30 min)
- ✅ Endpoint 7: Invite user (1 hour)
- ✅ Endpoint 8: Remove user (30 min)
- ✅ Endpoint 9: Update role (30 min)
- ✅ Endpoint 10: Get quotas (30 min)

### Step 3: Add Swagger Documentation (1 hour)
```python
# Add Flasgger decorators to all endpoints
@swag_from({
    'tags': ['Tenant Management'],
    'summary': 'List all tenants',
    'responses': {
        200: {'description': 'List of tenants'},
        403: {'description': 'Not authorized'}
    }
})
```

### Step 4: Testing (2-3 hours)
- ✅ Test all 10 endpoints with curl
- ✅ Test authorization (system admin, tenant admin, tenant member)
- ✅ Test quota enforcement
- ✅ Test error handling (validation, not found, access denied)

### Step 5: Documentation (1 hour)
- ✅ Update API documentation
- ✅ Create usage examples
- ✅ Document authorization requirements

**Total Estimated Time**: 8-11 hours (1-2 days)

---

## 🧪 TESTING PLAN

### 1. Authorization Tests

```bash
# Get tokens for different users
ADMIN_TOKEN=$(curl -X POST http://localhost:5002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@insa.com","password":"Admin123!"}' | jq -r .access_token)

# Test system admin access
curl http://localhost:5002/api/v1/tenants -H "Authorization: Bearer $ADMIN_TOKEN"
# Expected: 200 with list of tenants

# Test non-admin access
curl http://localhost:5002/api/v1/tenants -H "Authorization: Bearer $USER_TOKEN"
# Expected: 403 Access denied
```

### 2. CRUD Tests

```bash
# Create tenant
TENANT_ID=$(curl -X POST http://localhost:5002/api/v1/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Corp",
    "slug": "test-corp",
    "tier": "startup",
    "max_devices": 10,
    "max_users": 3
  }' | jq -r .id)

# Get tenant
curl http://localhost:5002/api/v1/tenants/$TENANT_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Expected: 200 with tenant details

# Update tenant
curl -X PATCH http://localhost:5002/api/v1/tenants/$TENANT_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier": "professional", "max_devices": 50}'
# Expected: 200 with updated tenant

# Get stats
curl http://localhost:5002/api/v1/tenants/$TENANT_ID/stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Expected: 200 with usage stats
```

### 3. User Management Tests

```bash
# List users
curl http://localhost:5002/api/v1/tenants/$TENANT_ID/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Expected: 200 with user list

# Invite user
curl -X POST http://localhost:5002/api/v1/tenants/$TENANT_ID/users/invite \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "role": "member"}'
# Expected: 201 with invitation

# Update role
curl -X PATCH http://localhost:5002/api/v1/tenants/$TENANT_ID/users/$USER_ID/role \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin", "is_tenant_admin": true}'
# Expected: 200 with updated role

# Remove user
curl -X DELETE http://localhost:5002/api/v1/tenants/$TENANT_ID/users/$USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Expected: 204 No Content
```

### 4. Quota Tests

```bash
# Get quotas
curl http://localhost:5002/api/v1/tenants/$TENANT_ID/quotas \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Expected: 200 with quota usage

# Test quota enforcement (create devices until limit)
for i in {1..11}; do
  curl -X POST http://localhost:5002/api/v1/devices \
    -H "Authorization: Bearer $TENANT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "Device '$i'", "device_type": "sensor"}'
done
# Expected: First 10 succeed (201), 11th fails (403 Quota exceeded)
```

---

## 📊 SUCCESS CRITERIA

### Functional Requirements
- ✅ All 10 endpoints implemented
- ✅ Authorization working (system admin, tenant admin, tenant member)
- ✅ Quota enforcement functional
- ✅ All CRUD operations working
- ✅ Error handling comprehensive (validation, not found, access denied)

### Quality Requirements
- ✅ Consistent code pattern across all endpoints
- ✅ Type hints and docstrings
- ✅ Error logging
- ✅ Swagger documentation
- ✅ Input validation

### Testing Requirements
- ✅ Manual testing with curl (all endpoints)
- ✅ Authorization testing (3 user types)
- ✅ Error handling testing
- ✅ Quota enforcement testing

---

## 🚀 DEPLOYMENT PLAN

### Step 1: Implementation (Day 1)
1. Add imports to app_advanced.py
2. Implement 10 endpoints (4-6 hours)
3. Add Swagger documentation (1 hour)

### Step 2: Testing (Day 1-2)
1. Manual testing with curl (2 hours)
2. Authorization testing (1 hour)
3. Error handling testing (1 hour)

### Step 3: Documentation (Day 2)
1. Update API documentation
2. Create usage examples
3. Write completion report

### Step 4: Deployment (Day 2)
1. Restart app_advanced.py
2. Verify all endpoints working
3. Update CLAUDE.md

**Total Timeline**: 1-2 days

---

## 📝 COMPLETION CRITERIA

**Phase 3 will be considered COMPLETE when**:
- ✅ All 10 tenant management endpoints implemented
- ✅ All endpoints documented in Swagger
- ✅ Authorization working correctly (3 user types)
- ✅ All manual tests passing
- ✅ Documentation updated
- ✅ CLAUDE.md updated with Phase 3 completion

**Next Phase**: Phase 4 (optional enhancements)
- Add PostgreSQL Row-Level Security (RLS)
- Performance testing with 10K+ devices
- Tenant switching UI component
- Audit logging for tenant operations

---

**Plan Created**: October 29, 2025 03:30 UTC
**Platform**: INSA Advanced IIoT Platform v2.0
**Feature**: Phase 3 Feature 6 (Multi-Tenancy) - Phase 3
**Status**: 📋 READY TO IMPLEMENT
**Estimated Duration**: 1-2 days

---

*Implementation plan by INSA Automation Corp*
*Platform: INSA Advanced IIoT Platform v2.0*
*Feature 6 Phase 3: Tenant Management API*

# Authentication System Documentation

## Overview

The Alkhorayef ESP IoT Platform uses **JWT (JSON Web Tokens)** for authentication with **Role-Based Access Control (RBAC)**. This document explains how to authenticate, manage users, and implement secure access to API endpoints.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication Flow](#authentication-flow)
3. [User Roles](#user-roles)
4. [API Endpoints](#api-endpoints)
5. [Token Management](#token-management)
6. [Security Best Practices](#security-best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Configure Environment

Set up JWT secret key in your `.env` file:

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
JWT_SECRET_KEY=your_generated_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7       # 7 days
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "created_at": "2025-11-20T10:00:00Z",
    "last_login": "2025-11-20T15:30:00Z"
  }
}
```

### 3. Use Access Token

Include the access token in subsequent requests:

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Authentication Flow

```
┌─────────┐                 ┌──────────┐                ┌──────────┐
│ Client  │                 │ API      │                │ Database │
└────┬────┘                 └────┬─────┘                └────┬─────┘
     │                           │                           │
     │ 1. POST /login            │                           │
     │ {username, password}      │                           │
     ├──────────────────────────>│                           │
     │                           │ 2. Verify credentials     │
     │                           ├──────────────────────────>│
     │                           │<──────────────────────────┤
     │                           │ 3. Generate JWT tokens    │
     │                           │                           │
     │ 4. Return tokens          │                           │
     │<──────────────────────────┤                           │
     │                           │                           │
     │ 5. API Request            │                           │
     │ Authorization: Bearer JWT │                           │
     ├──────────────────────────>│                           │
     │                           │ 6. Validate JWT           │
     │                           │                           │
     │                           │ 7. Check role permissions │
     │                           │                           │
     │ 8. Return data            │                           │
     │<──────────────────────────┤                           │
     │                           │                           │
```

### Token Lifecycle

1. **Login**: User authenticates with username/password
2. **Token Generation**: Server generates access token (24h) and refresh token (7d)
3. **Token Storage**: Client stores tokens securely
4. **API Requests**: Client includes access token in Authorization header
5. **Token Validation**: Server validates token signature and expiration
6. **Token Refresh**: When access token expires, use refresh token to get new access token
7. **Logout**: Client discards tokens, server invalidates refresh token

---

## User Roles

The system supports three roles with different permission levels:

### 1. Admin (`admin`)

**Full system access:**
- ✅ Create, read, update, delete users
- ✅ Access all telemetry data
- ✅ Run diagnostics
- ✅ System configuration
- ✅ View audit logs

**Example use case:** System administrators, DevOps engineers

### 2. Operator (`operator`)

**Operational access:**
- ✅ Read telemetry data
- ✅ Run diagnostics
- ✅ Create telemetry entries
- ❌ User management
- ❌ System configuration

**Example use case:** Field engineers, operators monitoring wells

### 3. Viewer (`viewer`)

**Read-only access:**
- ✅ Read telemetry data
- ✅ View diagnostics results
- ❌ Create/modify data
- ❌ Run diagnostics
- ❌ User management

**Example use case:** Management, auditors, stakeholders

---

## API Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/login

Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "Bearer",
  "user": {
    "id": 1,
    "username": "string",
    "role": "admin|operator|viewer",
    "created_at": "ISO8601 timestamp",
    "last_login": "ISO8601 timestamp"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing username or password
- `401 Unauthorized`: Invalid credentials
- `500 Internal Server Error`: Server error

---

#### POST /api/v1/auth/refresh

Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "string"
}
```

**Response (200 OK):**
```json
{
  "message": "Token refreshed successfully",
  "access_token": "string",
  "token_type": "Bearer"
}
```

**Error Responses:**
- `400 Bad Request`: Missing refresh token
- `401 Unauthorized`: Invalid or expired refresh token

---

#### POST /api/v1/auth/logout

Logout and invalidate tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request (Optional):**
```json
{
  "refresh_token": "string",
  "revoke_all_tokens": false
}
```

**Response (200 OK):**
```json
{
  "message": "Logout successful"
}
```

---

#### GET /api/v1/auth/me

Get current user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "username": "string",
    "role": "admin|operator|viewer",
    "created_at": "ISO8601 timestamp",
    "last_login": "ISO8601 timestamp"
  }
}
```

---

### User Management Endpoints (Admin Only)

#### GET /api/v1/auth/users

List all users.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "string",
      "role": "admin|operator|viewer",
      "created_at": "ISO8601 timestamp",
      "last_login": "ISO8601 timestamp"
    }
  ],
  "count": 1
}
```

---

#### POST /api/v1/auth/users

Create a new user.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Request:**
```json
{
  "username": "string",
  "password": "string (min 8 characters)",
  "role": "admin|operator|viewer"
}
```

**Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 2,
    "username": "string",
    "role": "admin|operator|viewer",
    "created_at": "ISO8601 timestamp"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input (weak password, invalid role)
- `409 Conflict`: Username already exists

---

## Token Management

### Access Tokens

- **Purpose:** Authenticate API requests
- **Expiration:** 24 hours (default)
- **Storage:** Client memory or secure storage
- **Usage:** Include in `Authorization` header

**Example:**
```http
GET /api/v1/telemetry/wells/WELL-001/latest HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Refresh Tokens

- **Purpose:** Obtain new access tokens without re-authentication
- **Expiration:** 7 days (default)
- **Storage:** Secure storage only (HttpOnly cookies, secure database)
- **Usage:** Send to `/api/v1/auth/refresh` endpoint

**Refresh Flow:**
```bash
# When access token expires
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### Token Structure

JWT tokens contain three parts: `header.payload.signature`

**Decoded Payload Example:**
```json
{
  "user_id": 1,
  "username": "admin",
  "role": "admin",
  "type": "access",
  "iat": 1700000000,  // Issued at
  "exp": 1700086400,  // Expires at
  "nbf": 1700000000   // Not before
}
```

---

## Security Best Practices

### 1. Secret Key Management

- **Generate strong keys:** Use at least 32 characters
- **Never commit secrets:** Add `.env` to `.gitignore`
- **Rotate regularly:** Change JWT_SECRET_KEY periodically
- **Use environment variables:** Never hardcode secrets

```bash
# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Token Storage

**Client-side:**
- ❌ **Never** store in localStorage (XSS vulnerable)
- ❌ **Never** store in sessionStorage (XSS vulnerable)
- ✅ Use HttpOnly cookies (web apps)
- ✅ Use secure device storage (mobile apps)
- ✅ Keep in memory when possible

**Server-side:**
- ✅ Store refresh tokens in database
- ✅ Hash tokens before storage
- ✅ Implement token revocation

### 3. Password Security

- ✅ Minimum 8 characters
- ✅ Require complexity (uppercase, lowercase, numbers, symbols)
- ✅ Use bcrypt for hashing (already implemented)
- ✅ Implement rate limiting on login attempts
- ✅ Change default passwords immediately

### 4. HTTPS/TLS

- ✅ **Always** use HTTPS in production
- ✅ Redirect HTTP to HTTPS
- ✅ Use strong TLS configurations
- ❌ **Never** send tokens over HTTP

### 5. Token Expiration

- ✅ Keep access tokens short-lived (15 minutes - 24 hours)
- ✅ Implement automatic token refresh
- ✅ Invalidate tokens on logout
- ✅ Clean up expired tokens regularly

### 6. Rate Limiting

Implement rate limiting on authentication endpoints:

```python
# Recommended limits
POST /api/v1/auth/login    -> 5 attempts per 5 minutes
POST /api/v1/auth/refresh  -> 10 attempts per hour
POST /api/v1/auth/users    -> 20 attempts per hour
```

---

## Protecting Your Endpoints

### Using the `@require_auth` Decorator

```python
from flask import Blueprint, jsonify
from app.core.auth import require_auth, get_current_user

api_bp = Blueprint("api", __name__)

# Any authenticated user
@api_bp.route("/data", methods=["GET"])
@require_auth()
def get_data():
    user = get_current_user()
    return jsonify({"data": "some data", "user": user["username"]})

# Admin only
@api_bp.route("/admin/config", methods=["POST"])
@require_auth(role="admin")
def update_config():
    return jsonify({"message": "Config updated"})

# Operator or Admin
@api_bp.route("/diagnostics", methods=["POST"])
@require_auth(role="operator")
def run_diagnostics():
    # Admins automatically have access
    return jsonify({"message": "Diagnostics started"})
```

### Permission Hierarchy

```
Admin > Operator > Viewer

Admin can access:
  - Admin endpoints
  - Operator endpoints
  - Viewer endpoints

Operator can access:
  - Operator endpoints
  - Viewer endpoints

Viewer can access:
  - Viewer endpoints only
```

---

## Troubleshooting

### Issue: "JWT_SECRET_KEY not configured"

**Cause:** Missing or empty JWT_SECRET_KEY in environment

**Solution:**
```bash
# Add to .env
JWT_SECRET_KEY=your_secure_key_at_least_32_chars
```

---

### Issue: "Token has expired"

**Cause:** Access token exceeded expiration time (default 24 hours)

**Solution:** Use refresh token to get new access token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

---

### Issue: "Invalid token"

**Causes:**
- Token tampered with
- Wrong JWT_SECRET_KEY
- Malformed token

**Solution:**
- Ensure JWT_SECRET_KEY is consistent across environments
- Re-authenticate to get fresh token
- Check token format: `Bearer <token>`

---

### Issue: "insufficient_permissions"

**Cause:** User role doesn't have access to endpoint

**Solution:**
- Check required role for endpoint
- Admin can create users with higher permissions
- Contact administrator for role upgrade

---

### Issue: "Authentication required but no token provided"

**Cause:** Missing Authorization header

**Solution:**
```bash
# Correct format
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Alternative (X-API-Key header)
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "X-API-Key: YOUR_ACCESS_TOKEN"
```

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);
```

### Refresh Tokens Table

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_used TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);
```

### Auth Audit Log Table

```sql
CREATE TABLE auth_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);
```

---

## Additional Resources

- [JWT.io](https://jwt.io/) - JWT debugger and documentation
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [RFC 7519 - JSON Web Token](https://tools.ietf.org/html/rfc7519)

---

## Support

For issues or questions:
- Check logs: `logs/alkhorayef-esp-platform.log`
- Review error responses for detailed messages
- Contact system administrator

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0

# Expert Architecture Plan: Part 2
## Security Engineering & Data Engineering Deep Dive

**Continuation of**: EXPERT_ARCHITECTURE_PLAN.md

---

# Part 2: Security Engineer Analysis

## 2.1 Current Security Posture Assessment

### Threat Model for Industrial IoT (Oil & Gas)

**Attack Surface Analysis**:
```
External Threats:
├── Internet-facing API (if exposed)
├── Tailscale network (VPN users)
├── Supply chain (dependencies)
└── Physical access (edge devices)

Internal Threats:
├── Insider access
├── Lateral movement
├── Data exfiltration
└── Privilege escalation

Specific to Oil & Gas:
├── SCADA system compromise
├── Sensor data manipulation
├── Diagnostic tampering
└── Intellectual property theft
```

### IEC 62443 Compliance Gap Analysis

| Requirement | IEC 62443-3-3 | Current Status | Gap | Priority |
|-------------|---------------|----------------|-----|----------|
| **IAC (Identification & Authentication Control)** ||||
| Unique user identification | SR 1.1 | ❌ None | CRITICAL | 🔴 P0 |
| Multi-factor authentication | SR 1.2 | ❌ None | HIGH | 🟡 P1 |
| Password management | SR 1.3 | ❌ None | CRITICAL | 🔴 P0 |
| **UC (Use Control)** ||||
| Authorization enforcement | SR 2.1 | ❌ None | CRITICAL | 🔴 P0 |
| Least privilege | SR 2.2 | ❌ None | HIGH | 🟡 P1 |
| Role-based access | SR 2.3 | ❌ None | CRITICAL | 🔴 P0 |
| **SI (System Integrity)** ||||
| Software integrity | SR 3.1 | ⚠️ Partial | MEDIUM | 🟢 P2 |
| Malware protection | SR 3.2 | ⚠️ Partial | MEDIUM | 🟢 P2 |
| **DC (Data Confidentiality)** ||||
| Encryption in transit | SR 4.1 | ⚠️ Tailscale only | HIGH | 🟡 P1 |
| Encryption at rest | SR 4.2 | ❌ None | HIGH | 🟡 P1 |
| **RDF (Restricted Data Flow)** ||||
| Network segmentation | SR 5.1 | ⚠️ Docker networks | MEDIUM | 🟢 P2 |
| Zone separation | SR 5.2 | ❌ None | HIGH | 🟡 P1 |
| **TRE (Timely Response to Events)** ||||
| Audit logging | SR 6.1 | ⚠️ Basic logs | CRITICAL | 🔴 P0 |
| SIEM integration | SR 6.2 | ❌ None | MEDIUM | 🟢 P2 |
| **RA (Resource Availability)** ||||
| DoS protection | SR 7.1 | ❌ None | HIGH | 🟡 P1 |
| Backup & recovery | SR 7.2 | ❌ None | CRITICAL | 🔴 P0 |

**Overall Compliance**: ~15% (Target: 80% for SL-2)

---

## 2.2 Authentication & Authorization Implementation

### JWT-Based Authentication System

```python
# app/core/security/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Settings
SECRET_KEY = settings.JWT_SECRET_KEY  # From environment/secrets
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

class SecurityService:
    """Authentication and authorization service"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password using Argon2"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash password using Argon2"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: timedelta = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    async def verify_token(token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )

            # Check token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            return payload

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Dependency injection
async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> dict:
    """Get current authenticated user from token"""
    payload = await SecurityService.verify_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Fetch user from database
    user = await UserRepository.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user

async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current active user"""
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user
```

### Role-Based Access Control (RBAC)

```python
# app/core/security/rbac.py
from enum import Enum
from typing import List
from fastapi import Depends, HTTPException, status

class Role(str, Enum):
    """User roles"""
    ADMIN = "admin"           # Full system access
    OPERATOR = "operator"     # Read/write telemetry, diagnostics
    ANALYST = "analyst"       # Read-only access, run diagnostics
    VIEWER = "viewer"         # Read-only access
    API_CLIENT = "api_client" # Machine-to-machine

class Permission(str, Enum):
    """Granular permissions"""
    # Telemetry
    TELEMETRY_READ = "telemetry:read"
    TELEMETRY_WRITE = "telemetry:write"
    TELEMETRY_DELETE = "telemetry:delete"

    # Diagnostics
    DIAGNOSTICS_READ = "diagnostics:read"
    DIAGNOSTICS_WRITE = "diagnostics:write"
    DIAGNOSTICS_RUN = "diagnostics:run"

    # Wells
    WELLS_READ = "wells:read"
    WELLS_WRITE = "wells:write"
    WELLS_DELETE = "wells:delete"

    # Users
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"

    # System
    SYSTEM_ADMIN = "system:admin"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        # All permissions
        Permission.TELEMETRY_READ,
        Permission.TELEMETRY_WRITE,
        Permission.TELEMETRY_DELETE,
        Permission.DIAGNOSTICS_READ,
        Permission.DIAGNOSTICS_WRITE,
        Permission.DIAGNOSTICS_RUN,
        Permission.WELLS_READ,
        Permission.WELLS_WRITE,
        Permission.WELLS_DELETE,
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.USERS_DELETE,
        Permission.SYSTEM_ADMIN,
    ],
    Role.OPERATOR: [
        Permission.TELEMETRY_READ,
        Permission.TELEMETRY_WRITE,
        Permission.DIAGNOSTICS_READ,
        Permission.DIAGNOSTICS_RUN,
        Permission.WELLS_READ,
    ],
    Role.ANALYST: [
        Permission.TELEMETRY_READ,
        Permission.DIAGNOSTICS_READ,
        Permission.DIAGNOSTICS_RUN,
        Permission.WELLS_READ,
    ],
    Role.VIEWER: [
        Permission.TELEMETRY_READ,
        Permission.DIAGNOSTICS_READ,
        Permission.WELLS_READ,
    ],
    Role.API_CLIENT: [
        Permission.TELEMETRY_WRITE,
        Permission.DIAGNOSTICS_RUN,
    ],
}

class RBACService:
    """Role-based access control service"""

    @staticmethod
    def has_permission(user: dict, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_role = Role(user.get("role", Role.VIEWER))
        allowed_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return permission in allowed_permissions

    @staticmethod
    def require_permission(permission: Permission):
        """Decorator to require specific permission"""
        async def permission_checker(
            current_user: dict = Depends(get_current_active_user)
        ):
            if not RBACService.has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )
            return current_user

        return permission_checker

    @staticmethod
    def require_role(allowed_roles: List[Role]):
        """Decorator to require specific role"""
        async def role_checker(
            current_user: dict = Depends(get_current_active_user)
        ):
            user_role = Role(current_user.get("role"))
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role not authorized: {user_role.value}"
                )
            return current_user

        return role_checker

# Usage in routes
@router.post("/telemetry/ingest")
async def ingest_telemetry(
    data: TelemetryData,
    current_user: dict = Depends(
        RBACService.require_permission(Permission.TELEMETRY_WRITE)
    )
):
    """Ingest telemetry - requires TELEMETRY_WRITE permission"""
    # ... implementation

@router.delete("/wells/{well_id}")
async def delete_well(
    well_id: str,
    current_user: dict = Depends(
        RBACService.require_role([Role.ADMIN])
    )
):
    """Delete well - admin only"""
    # ... implementation
```

### API Key Management (Machine-to-Machine)

```python
# app/core/security/api_keys.py
import secrets
from datetime import datetime, timedelta
from hashlib import sha256

class APIKeyService:
    """API key management for M2M authentication"""

    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate API key and its hash"""
        # Generate random key
        key = secrets.token_urlsafe(32)

        # Hash for storage
        key_hash = sha256(key.encode()).hexdigest()

        return key, key_hash

    @staticmethod
    async def create_api_key(
        name: str,
        permissions: List[Permission],
        expires_days: int = 365
    ) -> dict:
        """Create new API key"""
        key, key_hash = APIKeyService.generate_api_key()

        expires_at = datetime.utcnow() + timedelta(days=expires_days)

        api_key_data = {
            "key_hash": key_hash,
            "name": name,
            "permissions": [p.value for p in permissions],
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_active": True
        }

        # Store in database
        await APIKeyRepository.create(api_key_data)

        return {
            "key": key,  # Only returned once
            "name": name,
            "expires_at": expires_at
        }

    @staticmethod
    async def verify_api_key(key: str) -> dict:
        """Verify API key and return associated data"""
        key_hash = sha256(key.encode()).hexdigest()

        api_key = await APIKeyRepository.get_by_hash(key_hash)

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        if not api_key.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is inactive"
            )

        if datetime.utcnow() > api_key.get("expires_at"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired"
            )

        return api_key

# Dependency for API key authentication
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key_user(
    api_key: str = Depends(api_key_header)
) -> dict:
    """Authenticate using API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    key_data = await APIKeyService.verify_api_key(api_key)

    # Return user-like object for RBAC
    return {
        "id": key_data["id"],
        "name": key_data["name"],
        "role": Role.API_CLIENT,
        "permissions": key_data["permissions"],
        "is_active": True
    }
```

---

## 2.3 Secrets Management

### Current Problem
```yaml
# docker-compose.yml (INSECURE!)
environment:
  POSTGRES_PASSWORD: AlkhorayefESP2025!  # ❌ Plaintext
  REDIS_PASSWORD: RedisAlkhorayef2025!   # ❌ Plaintext
```

### Solution: HashiCorp Vault Integration

```yaml
# docker-compose.yml (SECURE)
services:
  vault:
    image: vault:1.15
    container_name: alkhorayef-vault
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: ${VAULT_ROOT_TOKEN}
      VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200"
    cap_add:
      - IPC_LOCK
    volumes:
      - vault_data:/vault/data
      - vault_logs:/vault/logs
      - ./vault/config:/vault/config
    command: server

  api:
    depends_on:
      - vault
    environment:
      - VAULT_ADDR=http://vault:8200
      - VAULT_TOKEN=${VAULT_TOKEN}
    # No more plaintext passwords!
```

```python
# app/core/security/vault.py
import hvac
from functools import lru_cache

class VaultService:
    """HashiCorp Vault integration"""

    def __init__(self):
        self.client = hvac.Client(
            url=settings.VAULT_ADDR,
            token=settings.VAULT_TOKEN
        )

    @lru_cache(maxsize=128)
    def get_secret(self, path: str, key: str) -> str:
        """Retrieve secret from Vault"""
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(
                path=path
            )
            return secret['data']['data'][key]
        except Exception as e:
            logger.error(f"Failed to retrieve secret {path}/{key}: {e}")
            raise

    def get_database_credentials(self) -> dict:
        """Get database credentials"""
        return {
            "username": self.get_secret("database/alkhorayef", "username"),
            "password": self.get_secret("database/alkhorayef", "password"),
            "host": self.get_secret("database/alkhorayef", "host"),
            "port": self.get_secret("database/alkhorayef", "port"),
            "database": self.get_secret("database/alkhorayef", "database")
        }

# Usage
vault = VaultService()
db_creds = vault.get_database_credentials()

DATABASE_URL = f"postgresql://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}:{db_creds['port']}/{db_creds['database']}"
```

### Vault Initialization Script

```bash
#!/bin/bash
# scripts/init-vault.sh

# Enable KV v2 secrets engine
vault secrets enable -path=secret kv-v2

# Store database credentials
vault kv put secret/database/alkhorayef \
  username=alkhorayef \
  password=$(openssl rand -base64 32) \
  host=timescaledb \
  port=5432 \
  database=esp_telemetry

# Store Redis credentials
vault kv put secret/redis/alkhorayef \
  password=$(openssl rand -base64 32)

# Store JWT secret
vault kv put secret/jwt \
  secret_key=$(openssl rand -base64 64)

# Create policy for API service
vault policy write alkhorayef-api - <<EOF
path "secret/data/database/alkhorayef" {
  capabilities = ["read"]
}

path "secret/data/redis/alkhorayef" {
  capabilities = ["read"]
}

path "secret/data/jwt" {
  capabilities = ["read"]
}
EOF

# Create token for API service
vault token create -policy=alkhorayef-api -period=24h
```

---

## 2.4 Encryption Implementation

### TLS for Internal Services

```yaml
# docker-compose-tls.yml
services:
  timescaledb:
    volumes:
      - ./certs/postgres:/var/lib/postgresql/certs:ro
    environment:
      - POSTGRES_SSL_MODE=require
      - POSTGRES_SSL_CERT_FILE=/var/lib/postgresql/certs/server.crt
      - POSTGRES_SSL_KEY_FILE=/var/lib/postgresql/certs/server.key
      - POSTGRES_SSL_CA_FILE=/var/lib/postgresql/certs/ca.crt

  redis:
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --tls-port 6380
      --port 0
      --tls-cert-file /certs/redis.crt
      --tls-key-file /certs/redis.key
      --tls-ca-cert-file /certs/ca.crt
    volumes:
      - ./certs/redis:/certs:ro
```

### Database Encryption at Rest

```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive fields
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    -- Store encrypted password hash
    password_hash BYTEA NOT NULL,
    -- Encrypt PII fields
    full_name_encrypted BYTEA,
    phone_encrypted BYTEA,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Helper functions
CREATE OR REPLACE FUNCTION encrypt_text(plaintext TEXT, key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(plaintext, key);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION decrypt_text(ciphertext BYTEA, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(ciphertext, key);
END;
$$ LANGUAGE plpgsql;
```

---

## 2.5 Audit Logging System

```python
# app/core/security/audit.py
from enum import Enum
from datetime import datetime
import json

class AuditEventType(str, Enum):
    """Audit event types"""
    # Authentication
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"

    # Authorization
    AUTHZ_ACCESS_GRANTED = "authz.access.granted"
    AUTHZ_ACCESS_DENIED = "authz.access.denied"

    # Data operations
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"

    # System
    SYSTEM_CONFIG_CHANGE = "system.config.change"
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"

class AuditLogger:
    """Comprehensive audit logging"""

    @staticmethod
    async def log_event(
        event_type: AuditEventType,
        user_id: str = None,
        resource_type: str = None,
        resource_id: str = None,
        action: str = None,
        outcome: str = "success",
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log audit event"""

        audit_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "resource": {
                "type": resource_type,
                "id": resource_id
            },
            "action": action,
            "outcome": outcome,
            "details": details or {},
            "metadata": {
                "ip_address": ip_address,
                "user_agent": user_agent
            }
        }

        # Log to file (structured JSON)
        logger.info(
            "AUDIT",
            extra={"audit_event": audit_event}
        )

        # Store in database for querying
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_log (
                    event_type, user_id, resource_type, resource_id,
                    action, outcome, details, ip_address, user_agent
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, event_type.value, user_id, resource_type, resource_id,
            action, outcome, json.dumps(details), ip_address, user_agent)

        # Send to SIEM (if configured)
        if settings.SIEM_ENABLED:
            await send_to_siem(audit_event)

# Middleware for automatic audit logging
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Audit all API requests"""

    start_time = time.time()

    # Extract user from token (if present)
    user_id = None
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            payload = await SecurityService.verify_token(token)
            user_id = payload.get("sub")
    except:
        pass

    # Process request
    response = await call_next(request)

    # Log audit event
    await AuditLogger.log_event(
        event_type=AuditEventType.DATA_READ if request.method == "GET"
                   else AuditEventType.DATA_CREATE if request.method == "POST"
                   else AuditEventType.DATA_UPDATE if request.method == "PUT"
                   else AuditEventType.DATA_DELETE if request.method == "DELETE"
                   else AuditEventType.AUTHZ_ACCESS_GRANTED,
        user_id=user_id,
        resource_type="api",
        resource_id=request.url.path,
        action=request.method,
        outcome="success" if response.status_code < 400 else "failure",
        details={
            "status_code": response.status_code,
            "duration_ms": round((time.time() - start_time) * 1000, 2)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    return response
```

### Audit Log Database Schema

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    action VARCHAR(50),
    outcome VARCHAR(20),
    details JSONB,
    ip_address INET,
    user_agent TEXT
);

-- Index for common queries
CREATE INDEX idx_audit_timestamp ON audit_log (timestamp DESC);
CREATE INDEX idx_audit_user ON audit_log (user_id, timestamp DESC);
CREATE INDEX idx_audit_resource ON audit_log (resource_type, resource_id, timestamp DESC);
CREATE INDEX idx_audit_event_type ON audit_log (event_type, timestamp DESC);

-- Partition by month for performance
SELECT create_hypertable('audit_log', 'timestamp');

-- Retention policy (keep 2 years for compliance)
SELECT add_retention_policy('audit_log', INTERVAL '2 years');
```

---

[CONTINUED...]

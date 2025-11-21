"""
Authentication and Authorization
=================================
JWT-based authentication with optional Keycloak integration
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# ====================================
# CONFIGURATION
# ====================================

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Keycloak Configuration (optional)
KEYCLOAK_ENABLED = os.getenv("KEYCLOAK_ENABLED", "false").lower() == "true"
KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL", "")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


# ====================================
# MODELS
# ====================================

class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: str
    tenant_id: str
    email: Optional[str] = None
    roles: list[str] = []
    permissions: list[str] = []


class Token(BaseModel):
    """Access and refresh tokens"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class User(BaseModel):
    """Current user information"""
    user_id: str
    tenant_id: str
    email: Optional[str] = None
    roles: list[str] = []
    permissions: list[str] = []


# ====================================
# PASSWORD UTILITIES
# ====================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ====================================
# JWT UTILITIES
# ====================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token

    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token

    Args:
        data: Payload data to encode

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def create_token_pair(user_id: str, tenant_id: str, **kwargs) -> Token:
    """
    Create both access and refresh tokens

    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        **kwargs: Additional claims (email, roles, permissions)

    Returns:
        Token object with both tokens
    """
    token_data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        **kwargs
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"user_id": user_id, "tenant_id": tenant_id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# ====================================
# AUTHENTICATION DEPENDENCIES
# ====================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user

    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.user_id}

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)

        # Validate token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Extract user data
        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")

        if not user_id or not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims"
            )

        return User(
            user_id=user_id,
            tenant_id=tenant_id,
            email=payload.get("email"),
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", [])
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    request: Request
) -> Optional[User]:
    """
    Optional authentication - returns None if no valid token

    Useful for endpoints that work both authenticated and unauthenticated
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")

    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")

        if user_id and tenant_id:
            return User(
                user_id=user_id,
                tenant_id=tenant_id,
                email=payload.get("email"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", [])
            )
    except:
        pass

    return None


# ====================================
# AUTHORIZATION HELPERS
# ====================================

def require_role(required_role: str):
    """
    Dependency factory to require a specific role

    Usage:
        @app.get("/admin")
        async def admin_route(user: User = Depends(require_role("admin"))):
            return {"message": "Welcome admin"}
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if required_role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return user
    return role_checker


def require_permission(required_permission: str):
    """
    Dependency factory to require a specific permission

    Usage:
        @app.delete("/device/{id}")
        async def delete_device(
            id: str,
            user: User = Depends(require_permission("device:delete"))
        ):
            return {"message": "Device deleted"}
    """
    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        if required_permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )
        return user
    return permission_checker


def require_any_role(required_roles: list[str]):
    """
    Dependency factory to require any of the specified roles

    Usage:
        @app.get("/moderator")
        async def mod_route(
            user: User = Depends(require_any_role(["admin", "moderator"]))
        ):
            return {"message": "Welcome"}
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {required_roles} required"
            )
        return user
    return role_checker


# ====================================
# DEMO USER (FOR TESTING)
# ====================================

async def get_demo_user() -> User:
    """
    Demo user for testing without authentication

    REMOVE THIS IN PRODUCTION!
    """
    return User(
        user_id="550e8400-e29b-41d4-a716-446655440000",
        tenant_id="660e8400-e29b-41d4-a716-446655440000",
        email="demo@insa-iot.com",
        roles=["user", "admin"],
        permissions=["*"]
    )


# ====================================
# KEYCLOAK INTEGRATION (OPTIONAL)
# ====================================

if KEYCLOAK_ENABLED:
    try:
        from keycloak import KeycloakOpenID

        keycloak_openid = KeycloakOpenID(
            server_url=KEYCLOAK_SERVER_URL,
            realm_name=KEYCLOAK_REALM,
            client_id=KEYCLOAK_CLIENT_ID,
            client_secret_key=KEYCLOAK_CLIENT_SECRET
        )

        async def verify_keycloak_token(token: str) -> Dict[str, Any]:
            """Verify token with Keycloak"""
            try:
                token_info = keycloak_openid.introspect(token)
                if not token_info.get("active"):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token is not active"
                    )
                return token_info
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Keycloak verification failed: {str(e)}"
                )

        print("✅ Keycloak integration enabled")

    except ImportError:
        print("⚠️  Keycloak enabled but python-keycloak not installed")
        print("   Install with: pip install python-keycloak")
        KEYCLOAK_ENABLED = False


# ====================================
# AUTHENTICATION MODE
# ====================================

def get_auth_mode() -> str:
    """Get current authentication mode"""
    if KEYCLOAK_ENABLED:
        return "Keycloak"
    elif SECRET_KEY == "your-secret-key-change-in-production":
        return "Demo (WARNING: Using default secret key!)"
    else:
        return "JWT"


print(f"🔐 Authentication mode: {get_auth_mode()}")

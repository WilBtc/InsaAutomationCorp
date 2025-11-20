"""
Rate Limiting Middleware for FastAPI.

This middleware applies rate limits to all incoming requests, extracting user
information from JWT tokens and applying appropriate limits based on role and endpoint.
"""

import time
from typing import Optional, Callable, Dict, Any

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import jwt

from app.core.rate_limiter import RateLimiter, RateLimitResult, TimeWindow
from app.core.logging import get_logger
from app.core.config import get_config

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits on API requests.

    Features:
    - Extracts user_id and role from JWT token
    - Checks rate limits before processing request
    - Returns 429 with Retry-After header if limit exceeded
    - Adds rate limit headers to all responses
    - Bypasses rate limiting for whitelisted paths
    """

    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = [
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico"
    ]

    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: RateLimiter,
        enable_rate_limiting: bool = True
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            rate_limiter: RateLimiter instance
            enable_rate_limiting: Global enable/disable flag
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.enabled = enable_rate_limiting
        self.config = get_config()

        logger.info(
            "Rate limit middleware initialized",
            extra={"enabled": self.enabled}
        )

    def _should_check_rate_limit(self, path: str) -> bool:
        """
        Determine if path should be rate limited.

        Args:
            path: Request path

        Returns:
            True if should check rate limit, False otherwise
        """
        # Check excluded paths
        for excluded in self.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return False

        return True

    def _extract_user_from_token(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract user information from JWT token.

        Args:
            request: FastAPI request

        Returns:
            Dictionary with user_id, username, and role or None
        """
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")

        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                self.config.security.jwt_secret_key,
                algorithms=[self.config.security.jwt_algorithm]
            )

            return {
                "user_id": str(payload.get("user_id", "anonymous")),
                "username": payload.get("username", "anonymous"),
                "role": payload.get("role", "anonymous")
            }

        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid JWT token: {e}")
            return None

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Handles X-Forwarded-For and X-Real-IP headers for proxied requests.

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For (may contain multiple IPs)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"

    def _add_rate_limit_headers(
        self,
        response: Response,
        result: RateLimitResult
    ) -> None:
        """
        Add rate limit headers to response.

        Args:
            response: FastAPI response
            result: Rate limit check result
        """
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_at)

        if not result.allowed and result.retry_after:
            response.headers["Retry-After"] = str(result.retry_after)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with rate limit headers
        """
        # Skip if rate limiting is disabled
        if not self.enabled:
            return await call_next(request)

        # Skip excluded paths
        if not self._should_check_rate_limit(request.url.path):
            return await call_next(request)

        # Extract user information
        user_info = self._extract_user_from_token(request)

        if user_info:
            user_id = user_info["user_id"]
            role = user_info["role"]
        else:
            # Anonymous user
            user_id = f"anon:{self._get_client_ip(request)}"
            role = "anonymous"

        # Get client IP for whitelisting
        client_ip = self._get_client_ip(request)

        # Check rate limit
        try:
            result = await self.rate_limiter.check_rate_limit(
                user_id=user_id,
                role=role,
                endpoint=request.url.path,
                ip_address=client_ip
            )

            # If rate limit exceeded, return 429
            if not result.allowed:
                logger.warning(
                    f"Rate limit exceeded for {user_id}",
                    extra={
                        "user_id": user_id,
                        "role": role,
                        "endpoint": request.url.path,
                        "ip": client_ip,
                        "retry_after": result.retry_after
                    }
                )

                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": "Too many requests. Please try again later.",
                        "limit": result.limit,
                        "retry_after": result.retry_after,
                        "reset_at": result.reset_at
                    }
                )

                self._add_rate_limit_headers(response, result)

                return response

            # Process request
            response = await call_next(request)

            # Add rate limit headers to successful response
            self._add_rate_limit_headers(response, result)

            return response

        except Exception as e:
            logger.error(
                f"Rate limit check error: {e}",
                extra={
                    "user_id": user_id,
                    "endpoint": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )

            # On error, allow request to proceed (fail open)
            # This prevents rate limiter issues from breaking the API
            return await call_next(request)


class EndpointRateLimiter:
    """
    Dependency injection for endpoint-specific rate limiting.

    Usage in FastAPI routes:
        @app.get("/api/v1/data")
        async def get_data(
            limiter: EndpointRateLimiter = Depends(get_endpoint_limiter)
        ):
            await limiter.check()
            ...
    """

    def __init__(
        self,
        rate_limiter: RateLimiter,
        request: Request,
        limit: Optional[int] = None,
        window: TimeWindow = TimeWindow.MINUTE
    ):
        """
        Initialize endpoint rate limiter.

        Args:
            rate_limiter: RateLimiter instance
            request: FastAPI request
            limit: Custom limit for this endpoint (optional)
            window: Time window for limit
        """
        self.rate_limiter = rate_limiter
        self.request = request
        self.custom_limit = limit
        self.window = window

    async def check(self, cost: int = 1) -> RateLimitResult:
        """
        Check rate limit for current request.

        Args:
            cost: Number of tokens to consume (default 1)

        Returns:
            Rate limit check result

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Extract user info
        auth_header = self.request.headers.get("Authorization")
        user_id = "anonymous"
        role = "anonymous"

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                config = get_config()
                payload = jwt.decode(
                    token,
                    config.security.jwt_secret_key,
                    algorithms=[config.security.jwt_algorithm]
                )
                user_id = str(payload.get("user_id", "anonymous"))
                role = payload.get("role", "anonymous")
            except jwt.InvalidTokenError:
                pass

        # Get client IP
        client_ip = self.request.client.host if self.request.client else "unknown"

        # Check rate limit
        result = await self.rate_limiter.check_rate_limit(
            user_id=user_id,
            role=role,
            endpoint=self.request.url.path,
            ip_address=client_ip
        )

        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": result.retry_after,
                    "reset_at": result.reset_at
                },
                headers={
                    "Retry-After": str(result.retry_after),
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": str(result.remaining),
                    "X-RateLimit-Reset": str(result.reset_at)
                }
            )

        return result


def get_endpoint_limiter(
    request: Request,
    rate_limiter: RateLimiter
) -> EndpointRateLimiter:
    """
    Dependency factory for endpoint rate limiter.

    Args:
        request: FastAPI request
        rate_limiter: RateLimiter instance (injected)

    Returns:
        EndpointRateLimiter instance
    """
    return EndpointRateLimiter(
        rate_limiter=rate_limiter,
        request=request
    )

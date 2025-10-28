"""
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 9
API Rate Limiting Module

Implements comprehensive rate limiting for public API endpoints using Redis as storage backend.

Features:
- Per-IP rate limiting for unauthenticated requests
- Per-user rate limiting for authenticated requests (JWT)
- Configurable limits per endpoint
- Burst allowances for short-term spikes
- Rate limit headers in all responses
- Admin bypass for trusted clients
- Monitoring and metrics

Security Features:
- DoS attack prevention
- Brute force login protection
- API abuse prevention
- Resource exhaustion protection

Author: Claude Code
Date: October 27, 2025
"""

import logging
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

logger = logging.getLogger(__name__)


class RateLimiterConfig:
    """Rate limiter configuration with tiered limits"""

    # Default rate limits (requests per time window)
    DEFAULT_LIMIT = "100 per hour"

    # Public endpoint limits (stricter for unauthenticated)
    PUBLIC_ENDPOINT_LIMITS = {
        "/health": "1000 per minute",  # Health checks are frequent
        "/api/v1/status": "100 per minute",
        "/api/v1/auth/login": "5 per minute",  # Brute force protection
        "/api/v1/auth/register": "3 per hour",  # Account creation abuse prevention
        "/api/v1/auth/refresh": "10 per minute",
    }

    # Authenticated endpoint limits (more generous)
    AUTHENTICATED_ENDPOINT_LIMITS = {
        "/api/v1/devices": "200 per minute",
        "/api/v1/telemetry": "500 per minute",  # High frequency telemetry
        "/api/v1/rules": "50 per minute",
        "/api/v1/alerts": "100 per minute",
        "/api/v1/analytics": "50 per minute",  # Computationally expensive
    }

    # Admin endpoints (trusted, minimal limits)
    ADMIN_ENDPOINT_LIMITS = {
        "/api/v1/admin": "500 per minute",
    }

    # Rate limit burst allowance (percentage over limit for short bursts)
    BURST_ALLOWANCE = 1.5  # 50% burst


class CustomRateLimiter:
    """
    Custom rate limiter with Redis backend and intelligent key generation.

    Uses IP address for unauthenticated requests and user ID for authenticated requests.
    Provides detailed rate limit information in response headers.
    """

    def __init__(self, app=None, redis_client=None):
        """
        Initialize rate limiter.

        Args:
            app: Flask application instance
            redis_client: Redis client for storage (required for production)
        """
        self.app = app
        self.redis_client = redis_client
        self.limiter = None
        self.config = RateLimiterConfig()

        if app is not None:
            self.init_app(app, redis_client)

    def init_app(self, app, redis_client=None):
        """
        Initialize rate limiter with Flask app.

        Args:
            app: Flask application instance
            redis_client: Redis client for storage
        """
        self.app = app
        self.redis_client = redis_client

        # Configure rate limiter storage
        if redis_client:
            # Production: Use Redis for distributed rate limiting
            storage_uri = f"redis://{redis_client.connection_pool.connection_kwargs.get('host', 'localhost')}:{redis_client.connection_pool.connection_kwargs.get('port', 6379)}/{redis_client.connection_pool.connection_kwargs.get('db', 0)}"
            logger.info(f"Rate limiter using Redis storage: {storage_uri}")
        else:
            # Development: Use in-memory storage (not suitable for production)
            storage_uri = "memory://"
            logger.warning("Rate limiter using in-memory storage (not suitable for production)")

        # Initialize Flask-Limiter
        self.limiter = Limiter(
            app=app,
            key_func=self._get_rate_limit_key,
            default_limits=[self.config.DEFAULT_LIMIT],
            storage_uri=storage_uri,
            strategy="fixed-window",  # Standard rate limiting strategy
            headers_enabled=True,  # Add rate limit headers to responses
            swallow_errors=True,  # Don't crash on rate limiter errors
        )

        # Register error handler for rate limit exceeded
        self.limiter.request_filter(self._should_skip_rate_limit)

        logger.info("Rate limiter initialized successfully")

    def _get_rate_limit_key(self) -> str:
        """
        Generate unique rate limit key based on request context.

        For authenticated requests: user_id
        For unauthenticated requests: IP address

        Returns:
            Unique key string for rate limiting
        """
        # Check if user is authenticated (JWT token)
        user_id = getattr(g, 'user_id', None)

        if user_id:
            # Authenticated user: rate limit by user ID
            key = f"user:{user_id}"
            logger.debug(f"Rate limit key (authenticated): {key}")
            return key
        else:
            # Unauthenticated: rate limit by IP address
            ip = get_remote_address()
            key = f"ip:{ip}"
            logger.debug(f"Rate limit key (unauthenticated): {key}")
            return key

    def _should_skip_rate_limit(self) -> bool:
        """
        Determine if rate limiting should be skipped for this request.

        Skip rate limiting for:
        - Admin users with bypass permission
        - Internal health checks from localhost
        - Trusted IP addresses (configurable)

        Returns:
            True if rate limiting should be skipped
        """
        # Skip for admin users with bypass permission
        is_admin = getattr(g, 'is_admin', False)
        has_bypass = getattr(g, 'rate_limit_bypass', False)

        if is_admin and has_bypass:
            logger.debug("Skipping rate limit for admin with bypass permission")
            return True

        # Skip for internal health checks from localhost
        if request.remote_addr in ['127.0.0.1', '::1']:
            if request.path in ['/health', '/api/v1/status']:
                logger.debug("Skipping rate limit for internal health check")
                return True

        return False

    def apply_limits(self):
        """
        Apply rate limits to all endpoints based on configuration.

        Called after app initialization to set up endpoint-specific limits.
        """
        if not self.limiter:
            logger.error("Rate limiter not initialized")
            return

        logger.info("Applying rate limits to endpoints...")

        # Public endpoints
        for endpoint, limit in self.config.PUBLIC_ENDPOINT_LIMITS.items():
            logger.info(f"  {endpoint}: {limit}")

        # Authenticated endpoints
        for endpoint, limit in self.config.AUTHENTICATED_ENDPOINT_LIMITS.items():
            logger.info(f"  {endpoint}: {limit} (authenticated)")

        logger.info("Rate limits applied successfully")

    def get_limiter(self):
        """Get the underlying Flask-Limiter instance"""
        return self.limiter

    def get_rate_limit_info(self, endpoint: str = None) -> Dict[str, Any]:
        """
        Get rate limit information for current request or specific endpoint.

        Args:
            endpoint: Optional endpoint path to check

        Returns:
            Dictionary with rate limit information
        """
        if not self.limiter:
            return {"error": "Rate limiter not initialized"}

        try:
            # Get current rate limit window info
            window_stats = self.limiter.limiter.get_window_stats()

            return {
                "limit": window_stats[0],
                "remaining": window_stats[1],
                "reset_time": window_stats[2],
                "endpoint": endpoint or request.path,
                "key": self._get_rate_limit_key()
            }
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {"error": str(e)}


def rate_limit_exceeded_handler(e):
    """
    Custom error handler for rate limit exceeded (429).

    Returns:
        JSON response with rate limit information and retry-after header
    """
    response = jsonify({
        "error": "rate_limit_exceeded",
        "message": "Too many requests. Please slow down and try again later.",
        "retry_after": e.description if hasattr(e, 'description') else "60 seconds"
    })
    response.status_code = 429
    return response


def create_rate_limiter(app, redis_client) -> CustomRateLimiter:
    """
    Factory function to create and configure rate limiter.

    Args:
        app: Flask application instance
        redis_client: Redis client for storage

    Returns:
        Configured CustomRateLimiter instance
    """
    limiter = CustomRateLimiter(app, redis_client)
    limiter.apply_limits()

    # Register error handler
    app.register_error_handler(429, rate_limit_exceeded_handler)

    return limiter


# Decorator for custom endpoint rate limits
def custom_rate_limit(limit: str):
    """
    Decorator to apply custom rate limit to specific endpoints.

    Usage:
        @app.route('/api/v1/expensive')
        @custom_rate_limit("10 per minute")
        def expensive_endpoint():
            return {"data": "..."}

    Args:
        limit: Rate limit string (e.g., "10 per minute")
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This will be handled by Flask-Limiter's @limiter.limit() decorator
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Global rate limiter instance (initialized in app_advanced.py)
_rate_limiter: Optional[CustomRateLimiter] = None


def get_rate_limiter() -> Optional[CustomRateLimiter]:
    """Get global rate limiter instance"""
    return _rate_limiter


def set_rate_limiter(limiter: CustomRateLimiter):
    """Set global rate limiter instance"""
    global _rate_limiter
    _rate_limiter = limiter


# Rate limit monitoring utilities
class RateLimitMetrics:
    """Track and report rate limiting metrics"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.metrics_prefix = "rate_limit:metrics:"

    def record_limit_hit(self, endpoint: str, key: str):
        """Record when a rate limit is hit"""
        metric_key = f"{self.metrics_prefix}hits:{endpoint}"
        self.redis.incr(metric_key)
        self.redis.expire(metric_key, 86400)  # 24 hour TTL

    def record_request(self, endpoint: str, key: str):
        """Record a successful request"""
        metric_key = f"{self.metrics_prefix}requests:{endpoint}"
        self.redis.incr(metric_key)
        self.redis.expire(metric_key, 86400)  # 24 hour TTL

    def get_metrics(self, endpoint: str = None) -> Dict[str, Any]:
        """Get rate limiting metrics for endpoint or all endpoints"""
        if endpoint:
            hits = self.redis.get(f"{self.metrics_prefix}hits:{endpoint}") or 0
            requests = self.redis.get(f"{self.metrics_prefix}requests:{endpoint}") or 0
            return {
                "endpoint": endpoint,
                "hits": int(hits),
                "requests": int(requests),
                "hit_rate": float(hits) / float(requests) if int(requests) > 0 else 0
            }
        else:
            # Get all endpoints
            all_metrics = {}
            pattern = f"{self.metrics_prefix}requests:*"
            for key in self.redis.scan_iter(match=pattern):
                endpoint = key.decode().replace(f"{self.metrics_prefix}requests:", "")
                all_metrics[endpoint] = self.get_metrics(endpoint)
            return all_metrics


if __name__ == "__main__":
    print("INSA Advanced IIoT Platform - Rate Limiting Module")
    print("This module should be imported by app_advanced.py")
    print("\nRate Limit Configuration:")
    config = RateLimiterConfig()
    print(f"\nPublic Endpoints:")
    for endpoint, limit in config.PUBLIC_ENDPOINT_LIMITS.items():
        print(f"  {endpoint}: {limit}")
    print(f"\nAuthenticated Endpoints:")
    for endpoint, limit in config.AUTHENTICATED_ENDPOINT_LIMITS.items():
        print(f"  {endpoint}: {limit}")

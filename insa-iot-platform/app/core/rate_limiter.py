"""
Token Bucket Rate Limiter with Redis Backend for Distributed Rate Limiting.

This module provides a production-ready rate limiting implementation using the
token bucket algorithm with atomic Redis operations via Lua scripts.

Features:
- Token bucket algorithm with automatic refill
- Distributed rate limiting across multiple workers
- Per-user, per-endpoint, and global limits
- Role-based rate limits (admin, operator, viewer)
- Burst handling (allow short spikes)
- IP whitelist for bypass
- Prometheus metrics integration
- <1ms overhead per request
"""

import time
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
from functools import wraps

import redis.asyncio as redis
from prometheus_client import Counter, Gauge, Histogram

from .logging import get_logger
from .exceptions import RateLimitExceeded

logger = get_logger(__name__)


# Prometheus metrics
rate_limit_checks_total = Counter(
    'rate_limit_checks_total',
    'Total rate limit checks',
    ['result', 'limit_type', 'role']
)

rate_limit_remaining_gauge = Gauge(
    'rate_limit_remaining',
    'Remaining rate limit tokens',
    ['user_id', 'window', 'limit_type']
)

rate_limit_check_duration = Histogram(
    'rate_limit_check_duration_seconds',
    'Time spent checking rate limits',
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1]
)


class LimitType(str, Enum):
    """Rate limit types."""

    USER = "user"
    ENDPOINT = "endpoint"
    GLOBAL = "global"
    IP = "ip"


class TimeWindow(str, Enum):
    """Time windows for rate limiting."""

    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass
class RateLimit:
    """Rate limit configuration."""

    limit: int  # Maximum requests
    window: TimeWindow  # Time window
    burst_multiplier: float = 2.0  # Allow burst up to 2x for short periods
    burst_duration_seconds: int = 10  # Burst allowance duration


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: int  # Unix timestamp
    retry_after: Optional[int] = None  # Seconds until reset (if denied)


# Lua script for atomic token bucket operations
# This ensures race conditions are impossible in distributed environments
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local burst_limit = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

-- Get current bucket state
local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
local tokens = tonumber(bucket[1])
local last_update = tonumber(bucket[2])

-- Initialize if doesn't exist
if not tokens or not last_update then
    tokens = limit
    last_update = now
end

-- Calculate tokens to add based on elapsed time
local elapsed = now - last_update
local refill_rate = limit / window_seconds
local tokens_to_add = elapsed * refill_rate

-- Refill tokens (capped at burst limit)
tokens = math.min(burst_limit, tokens + tokens_to_add)

-- Try to consume one token
local allowed = 0
local remaining = tokens

if tokens >= 1 then
    tokens = tokens - 1
    remaining = tokens
    allowed = 1
end

-- Update bucket state
redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
redis.call('EXPIRE', key, window_seconds * 2)  -- Auto-cleanup

-- Calculate reset time
local reset_at = now + window_seconds

return {allowed, math.floor(remaining), reset_at}
"""


class RateLimiter:
    """
    Token bucket rate limiter with Redis backend.

    Implements distributed rate limiting with atomic operations using Lua scripts.
    Supports multiple limit tiers and burst handling.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        default_limits: Dict[str, Dict[TimeWindow, int]],
        endpoint_overrides: Optional[Dict[str, Dict[TimeWindow, int]]] = None,
        whitelisted_ips: Optional[List[str]] = None,
        global_limit: Optional[RateLimit] = None
    ):
        """
        Initialize rate limiter.

        Args:
            redis_client: Redis client instance
            default_limits: Default limits per role
            endpoint_overrides: Per-endpoint limit overrides
            whitelisted_ips: IP addresses to bypass rate limiting
            global_limit: Global rate limit across all users
        """
        self.redis = redis_client
        self.default_limits = default_limits
        self.endpoint_overrides = endpoint_overrides or {}
        self.whitelisted_ips = set(whitelisted_ips or [])
        self.global_limit = global_limit

        # Load Lua script
        self._script_sha: Optional[str] = None

        logger.info(
            "Rate limiter initialized",
            extra={
                "roles": list(default_limits.keys()),
                "endpoint_overrides": len(self.endpoint_overrides),
                "whitelisted_ips": len(self.whitelisted_ips)
            }
        )

    async def _ensure_script_loaded(self) -> str:
        """Ensure Lua script is loaded in Redis."""
        if not self._script_sha:
            self._script_sha = await self.redis.script_load(TOKEN_BUCKET_SCRIPT)
        return self._script_sha

    def _get_window_seconds(self, window: TimeWindow) -> int:
        """Convert time window to seconds."""
        mapping = {
            TimeWindow.SECOND: 1,
            TimeWindow.MINUTE: 60,
            TimeWindow.HOUR: 3600,
            TimeWindow.DAY: 86400
        }
        return mapping[window]

    def _get_rate_limit(
        self,
        role: str,
        endpoint: Optional[str],
        window: TimeWindow
    ) -> Optional[RateLimit]:
        """
        Get rate limit for role and endpoint.

        Priority:
        1. Endpoint-specific override
        2. Role default
        3. None if not found
        """
        # Check endpoint override first
        if endpoint and endpoint in self.endpoint_overrides:
            override_limits = self.endpoint_overrides[endpoint]
            if window in override_limits:
                return RateLimit(
                    limit=override_limits[window],
                    window=window
                )

        # Fall back to role default
        if role in self.default_limits:
            role_limits = self.default_limits[role]
            if window in role_limits:
                return RateLimit(
                    limit=role_limits[window],
                    window=window
                )

        return None

    async def _check_limit_with_script(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        burst_multiplier: float
    ) -> Tuple[int, int, int]:
        """
        Check rate limit using Lua script (atomic operation).

        Returns:
            Tuple of (allowed, remaining, reset_at)
        """
        script_sha = await self._ensure_script_loaded()
        now = time.time()
        burst_limit = int(limit * burst_multiplier)

        result = await self.redis.evalsha(
            script_sha,
            1,  # Number of keys
            key,
            limit,
            window_seconds,
            burst_limit,
            now
        )

        return int(result[0]), int(result[1]), int(result[2])

    async def check_rate_limit(
        self,
        user_id: str,
        role: str,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        windows: Optional[List[TimeWindow]] = None
    ) -> RateLimitResult:
        """
        Check if request is within rate limits.

        Args:
            user_id: User identifier
            role: User role (admin, operator, viewer)
            endpoint: API endpoint path
            ip_address: Client IP address
            windows: Time windows to check (default: [MINUTE, HOUR, DAY])

        Returns:
            RateLimitResult with decision and metadata

        Raises:
            Does not raise, returns result with allowed=False
        """
        start_time = time.time()

        try:
            # Check IP whitelist
            if ip_address and ip_address in self.whitelisted_ips:
                logger.debug(f"IP {ip_address} is whitelisted, bypassing rate limit")
                return RateLimitResult(
                    allowed=True,
                    limit=999999,
                    remaining=999999,
                    reset_at=int(time.time() + 3600)
                )

            # Default windows to check
            if windows is None:
                windows = [TimeWindow.MINUTE, TimeWindow.HOUR, TimeWindow.DAY]

            # Check each time window
            for window in windows:
                rate_limit = self._get_rate_limit(role, endpoint, window)

                if not rate_limit:
                    continue

                # Build Redis key
                endpoint_part = hashlib.md5(endpoint.encode()).hexdigest()[:8] if endpoint else "global"
                key = f"rate_limit:{user_id}:{endpoint_part}:{window.value}"

                # Check limit using atomic Lua script
                window_seconds = self._get_window_seconds(window)
                allowed, remaining, reset_at = await self._check_limit_with_script(
                    key,
                    rate_limit.limit,
                    window_seconds,
                    rate_limit.burst_multiplier
                )

                # Update metrics
                result_label = "allowed" if allowed else "denied"
                rate_limit_checks_total.labels(
                    result=result_label,
                    limit_type=LimitType.USER.value,
                    role=role
                ).inc()

                rate_limit_remaining_gauge.labels(
                    user_id=user_id,
                    window=window.value,
                    limit_type=LimitType.USER.value
                ).set(remaining)

                # If denied, return immediately
                if not allowed:
                    retry_after = reset_at - int(time.time())

                    logger.warning(
                        f"Rate limit exceeded for user {user_id}",
                        extra={
                            "user_id": user_id,
                            "role": role,
                            "endpoint": endpoint,
                            "window": window.value,
                            "limit": rate_limit.limit,
                            "retry_after": retry_after
                        }
                    )

                    return RateLimitResult(
                        allowed=False,
                        limit=rate_limit.limit,
                        remaining=0,
                        reset_at=reset_at,
                        retry_after=retry_after
                    )

            # Check global limit if configured
            if self.global_limit:
                key = f"rate_limit:global:{self.global_limit.window.value}"
                window_seconds = self._get_window_seconds(self.global_limit.window)

                allowed, remaining, reset_at = await self._check_limit_with_script(
                    key,
                    self.global_limit.limit,
                    window_seconds,
                    self.global_limit.burst_multiplier
                )

                if not allowed:
                    retry_after = reset_at - int(time.time())

                    logger.warning(
                        "Global rate limit exceeded",
                        extra={
                            "limit": self.global_limit.limit,
                            "window": self.global_limit.window.value,
                            "retry_after": retry_after
                        }
                    )

                    rate_limit_checks_total.labels(
                        result="denied",
                        limit_type=LimitType.GLOBAL.value,
                        role=role
                    ).inc()

                    return RateLimitResult(
                        allowed=False,
                        limit=self.global_limit.limit,
                        remaining=0,
                        reset_at=reset_at,
                        retry_after=retry_after
                    )

            # All checks passed
            return RateLimitResult(
                allowed=True,
                limit=rate_limit.limit if rate_limit else 999999,
                remaining=remaining,
                reset_at=reset_at
            )

        finally:
            # Record check duration
            duration = time.time() - start_time
            rate_limit_check_duration.observe(duration)

            if duration > 0.001:  # Log if >1ms
                logger.warning(
                    f"Rate limit check took {duration*1000:.2f}ms (target <1ms)",
                    extra={"duration_ms": duration * 1000}
                )

    async def reset_user_limits(self, user_id: str) -> int:
        """
        Reset all rate limits for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of keys deleted
        """
        pattern = f"rate_limit:{user_id}:*"
        keys = []

        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted = await self.redis.delete(*keys)
            logger.info(f"Reset rate limits for user {user_id}", extra={"keys_deleted": deleted})
            return deleted

        return 0

    async def get_user_status(
        self,
        user_id: str,
        role: str
    ) -> Dict[str, Any]:
        """
        Get current rate limit status for a user.

        Args:
            user_id: User identifier
            role: User role

        Returns:
            Dictionary with limit status for each window
        """
        status = {}

        for window in [TimeWindow.MINUTE, TimeWindow.HOUR, TimeWindow.DAY]:
            rate_limit = self._get_rate_limit(role, None, window)

            if not rate_limit:
                continue

            key = f"rate_limit:{user_id}:global:{window.value}"
            bucket = await self.redis.hmget(key, 'tokens', 'last_update')

            tokens = float(bucket[0]) if bucket[0] else rate_limit.limit
            last_update = float(bucket[1]) if bucket[1] else time.time()

            # Calculate current tokens with refill
            now = time.time()
            elapsed = now - last_update
            window_seconds = self._get_window_seconds(window)
            refill_rate = rate_limit.limit / window_seconds
            tokens = min(rate_limit.limit, tokens + (elapsed * refill_rate))

            status[window.value] = {
                "limit": rate_limit.limit,
                "remaining": int(tokens),
                "reset_at": int(now + window_seconds),
                "usage_percent": ((rate_limit.limit - tokens) / rate_limit.limit) * 100
            }

        return status

    async def get_top_consumers(
        self,
        limit: int = 10,
        window: TimeWindow = TimeWindow.MINUTE
    ) -> List[Dict[str, Any]]:
        """
        Get top rate limit consumers (users with highest usage).

        Args:
            limit: Number of top consumers to return
            window: Time window to analyze

        Returns:
            List of top consumers with usage statistics
        """
        pattern = f"rate_limit:*:global:{window.value}"
        consumers = []

        async for key in self.redis.scan_iter(match=pattern):
            # Extract user_id from key
            parts = key.split(':')
            if len(parts) >= 2:
                user_id = parts[1]

                bucket = await self.redis.hmget(key, 'tokens', 'last_update')
                if bucket[0]:
                    tokens = float(bucket[0])
                    # Assume a reasonable default limit if not known
                    # In practice, you'd look up the actual limit
                    consumers.append({
                        "user_id": user_id,
                        "tokens_remaining": tokens,
                        "key": key
                    })

        # Sort by tokens remaining (lowest = highest usage)
        consumers.sort(key=lambda x: x["tokens_remaining"])

        return consumers[:limit]


def rate_limit(
    limit: int,
    per: str = "minute",
    burst_multiplier: float = 2.0
):
    """
    Decorator to apply custom rate limits to specific endpoints.

    Usage:
        @rate_limit(limit=50, per="minute")
        async def expensive_endpoint():
            pass

    Args:
        limit: Maximum requests
        per: Time window ("second", "minute", "hour", "day")
        burst_multiplier: Burst allowance multiplier
    """
    def decorator(func):
        # Store rate limit metadata on function
        func._rate_limit = RateLimit(
            limit=limit,
            window=TimeWindow(per.lower()),
            burst_multiplier=burst_multiplier
        )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Default rate limit configurations
DEFAULT_RATE_LIMITS = {
    "admin": {
        TimeWindow.SECOND: 50,
        TimeWindow.MINUTE: 1000,
        TimeWindow.HOUR: 50000,
        TimeWindow.DAY: 1000000
    },
    "operator": {
        TimeWindow.SECOND: 25,
        TimeWindow.MINUTE: 500,
        TimeWindow.HOUR: 25000,
        TimeWindow.DAY: 500000
    },
    "viewer": {
        TimeWindow.SECOND: 5,
        TimeWindow.MINUTE: 100,
        TimeWindow.HOUR: 5000,
        TimeWindow.DAY: 100000
    },
    "anonymous": {
        TimeWindow.SECOND: 2,
        TimeWindow.MINUTE: 10,
        TimeWindow.HOUR: 100,
        TimeWindow.DAY: 1000
    }
}

# Endpoint-specific overrides
ENDPOINT_OVERRIDES = {
    "/api/v1/telemetry/batch": {
        TimeWindow.MINUTE: 50,
        TimeWindow.HOUR: 1000
    },
    "/api/v1/ml/train": {
        TimeWindow.HOUR: 10,
        TimeWindow.DAY: 50
    },
    "/api/v1/diagnostics/decision_tree": {
        TimeWindow.MINUTE: 100,
        TimeWindow.HOUR: 5000
    }
}


async def create_rate_limiter(redis_client: redis.Redis) -> RateLimiter:
    """
    Factory function to create a configured rate limiter.

    Args:
        redis_client: Redis client instance

    Returns:
        Configured RateLimiter instance
    """
    # Global rate limit: 10,000 req/min across all users
    global_limit = RateLimit(
        limit=10000,
        window=TimeWindow.MINUTE,
        burst_multiplier=1.5
    )

    limiter = RateLimiter(
        redis_client=redis_client,
        default_limits=DEFAULT_RATE_LIMITS,
        endpoint_overrides=ENDPOINT_OVERRIDES,
        global_limit=global_limit
    )

    logger.info("Rate limiter created successfully")

    return limiter

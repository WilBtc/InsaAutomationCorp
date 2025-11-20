"""
Quota Service for Multi-Tenancy

This service handles quota enforcement using Redis for fast, atomic counters:
- API call tracking (hourly and daily)
- Storage usage monitoring
- Concurrent request limiting
- Quota warnings and hard limits
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import redis
from app.core.logging import get_logger
from app.core.exceptions import QuotaExceededError

logger = get_logger(__name__)


class QuotaService:
    """Service for quota enforcement and tracking."""

    def __init__(self, db_pool, redis_client: Optional[redis.Redis] = None):
        """
        Initialize quota service.

        Args:
            db_pool: Database connection pool
            redis_client: Redis client for quota counters (optional)
        """
        self.db_pool = db_pool

        # Initialize Redis client if not provided
        if redis_client is None:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_QUOTA_DB", "1"))
            redis_password = os.getenv("REDIS_PASSWORD", None)

            try:
                self.redis = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis.ping()
                self.redis_available = True
                logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis not available, quota tracking will be database-only: {e}")
                self.redis = None
                self.redis_available = False
        else:
            self.redis = redis_client
            self.redis_available = True

        # Quota warning thresholds
        self.warning_threshold = 0.8  # 80%
        self.critical_threshold = 0.95  # 95%

    def _get_hour_key(self, tenant_id: int) -> str:
        """Get Redis key for current hour."""
        hour = datetime.utcnow().strftime("%Y%m%d%H")
        return f"quota:api:hour:{tenant_id}:{hour}"

    def _get_day_key(self, tenant_id: int) -> str:
        """Get Redis key for current day."""
        day = datetime.utcnow().strftime("%Y%m%d")
        return f"quota:api:day:{tenant_id}:{day}"

    def _get_concurrent_key(self, tenant_id: int) -> str:
        """Get Redis key for concurrent requests."""
        return f"quota:concurrent:{tenant_id}"

    def check_and_increment_api_quota(
        self,
        tenant_id: int,
        endpoint: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if tenant is within API quota and increment counter.

        This is atomic - if quota is not exceeded, counter is incremented.

        Args:
            tenant_id: Tenant ID
            endpoint: API endpoint (for logging)

        Returns:
            Tuple of (allowed: bool, quota_info: dict)

        Raises:
            QuotaExceededError: If quota exceeded
        """
        try:
            # Get tenant quotas from database
            result = self.db_pool.execute_query(
                """
                SELECT api_calls_per_hour, api_calls_per_day, api_burst_limit
                FROM tenant_quotas
                WHERE tenant_id = %s
                """,
                (tenant_id,),
                fetch=True
            )

            if not result:
                # No quotas defined, allow (shouldn't happen)
                logger.warning(f"No quotas found for tenant {tenant_id}")
                return True, {"allowed": True, "reason": "no_quotas_defined"}

            hourly_limit = result[0][0]
            daily_limit = result[0][1]
            burst_limit = result[0][2]

            if not self.redis_available:
                # Fall back to database-based tracking (slower)
                return self._check_quota_database(tenant_id, hourly_limit, daily_limit)

            # Get current counts from Redis
            hour_key = self._get_hour_key(tenant_id)
            day_key = self._get_day_key(tenant_id)

            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()
            pipe.get(hour_key)
            pipe.get(day_key)
            pipe.get(self._get_concurrent_key(tenant_id))
            results = pipe.execute()

            hour_count = int(results[0]) if results[0] else 0
            day_count = int(results[1]) if results[1] else 0
            concurrent_count = int(results[2]) if results[2] else 0

            # Check hourly limit
            if hour_count >= hourly_limit:
                logger.warning(
                    f"Hourly API quota exceeded for tenant {tenant_id}",
                    extra={
                        "extra_fields": {
                            "tenant_id": tenant_id,
                            "current": hour_count,
                            "limit": hourly_limit,
                            "endpoint": endpoint
                        }
                    }
                )
                raise QuotaExceededError(
                    message="Hourly API quota exceeded",
                    details={
                        "quota_type": "hourly",
                        "current": hour_count,
                        "limit": hourly_limit,
                        "reset_at": self._get_hour_reset_time()
                    }
                )

            # Check daily limit
            if day_count >= daily_limit:
                logger.warning(
                    f"Daily API quota exceeded for tenant {tenant_id}",
                    extra={
                        "extra_fields": {
                            "tenant_id": tenant_id,
                            "current": day_count,
                            "limit": daily_limit,
                            "endpoint": endpoint
                        }
                    }
                )
                raise QuotaExceededError(
                    message="Daily API quota exceeded",
                    details={
                        "quota_type": "daily",
                        "current": day_count,
                        "limit": daily_limit,
                        "reset_at": self._get_day_reset_time()
                    }
                )

            # Check concurrent limit (burst protection)
            if concurrent_count >= burst_limit:
                logger.warning(
                    f"Concurrent request limit exceeded for tenant {tenant_id}",
                    extra={
                        "extra_fields": {
                            "tenant_id": tenant_id,
                            "current": concurrent_count,
                            "limit": burst_limit,
                            "endpoint": endpoint
                        }
                    }
                )
                raise QuotaExceededError(
                    message="Too many concurrent requests",
                    details={
                        "quota_type": "concurrent",
                        "current": concurrent_count,
                        "limit": burst_limit
                    }
                )

            # Increment counters (atomic)
            pipe = self.redis.pipeline()

            # Increment hour counter with expiry
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)  # 1 hour TTL

            # Increment day counter with expiry
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)  # 24 hour TTL

            # Increment concurrent counter
            pipe.incr(self._get_concurrent_key(tenant_id))

            results = pipe.execute()

            new_hour_count = results[0]
            new_day_count = results[2]

            # Check if warning threshold reached
            hour_percent = new_hour_count / hourly_limit
            day_percent = new_day_count / daily_limit

            warning_level = None
            if hour_percent >= self.critical_threshold or day_percent >= self.critical_threshold:
                warning_level = "critical"
            elif hour_percent >= self.warning_threshold or day_percent >= self.warning_threshold:
                warning_level = "warning"

            if warning_level:
                logger.warning(
                    f"Quota {warning_level} for tenant {tenant_id}",
                    extra={
                        "extra_fields": {
                            "tenant_id": tenant_id,
                            "hour_usage": f"{hour_percent*100:.1f}%",
                            "day_usage": f"{day_percent*100:.1f}%",
                            "warning_level": warning_level
                        }
                    }
                )

            return True, {
                "allowed": True,
                "hourly": {
                    "current": new_hour_count,
                    "limit": hourly_limit,
                    "percent": round(hour_percent * 100, 2)
                },
                "daily": {
                    "current": new_day_count,
                    "limit": daily_limit,
                    "percent": round(day_percent * 100, 2)
                },
                "concurrent": {
                    "current": concurrent_count + 1,
                    "limit": burst_limit
                },
                "warning_level": warning_level
            }

        except QuotaExceededError:
            raise
        except Exception as e:
            logger.error(f"Error checking quota for tenant {tenant_id}: {e}", exc_info=e)
            # Fail open - allow request but log error
            return True, {"allowed": True, "reason": "quota_check_failed", "error": str(e)}

    def _check_quota_database(
        self,
        tenant_id: int,
        hourly_limit: int,
        daily_limit: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Fallback quota checking using database (when Redis unavailable).

        Args:
            tenant_id: Tenant ID
            hourly_limit: Hourly API call limit
            daily_limit: Daily API call limit

        Returns:
            Tuple of (allowed: bool, quota_info: dict)
        """
        try:
            # Count API calls in last hour
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            result = self.db_pool.execute_query(
                """
                SELECT COUNT(*)
                FROM auth_audit_log
                WHERE user_id IN (SELECT user_id FROM tenant_users WHERE tenant_id = %s)
                  AND timestamp > %s
                  AND action LIKE 'api_%'
                """,
                (tenant_id, hour_ago),
                fetch=True
            )
            hour_count = result[0][0] if result else 0

            # Count API calls in last day
            day_ago = datetime.utcnow() - timedelta(days=1)
            result = self.db_pool.execute_query(
                """
                SELECT COUNT(*)
                FROM auth_audit_log
                WHERE user_id IN (SELECT user_id FROM tenant_users WHERE tenant_id = %s)
                  AND timestamp > %s
                  AND action LIKE 'api_%'
                """,
                (tenant_id, day_ago),
                fetch=True
            )
            day_count = result[0][0] if result else 0

            # Check limits
            if hour_count >= hourly_limit:
                raise QuotaExceededError(
                    message="Hourly API quota exceeded",
                    details={
                        "quota_type": "hourly",
                        "current": hour_count,
                        "limit": hourly_limit
                    }
                )

            if day_count >= daily_limit:
                raise QuotaExceededError(
                    message="Daily API quota exceeded",
                    details={
                        "quota_type": "daily",
                        "current": day_count,
                        "limit": daily_limit
                    }
                )

            return True, {
                "allowed": True,
                "method": "database",
                "hourly": {"current": hour_count, "limit": hourly_limit},
                "daily": {"current": day_count, "limit": daily_limit}
            }

        except QuotaExceededError:
            raise
        except Exception as e:
            logger.error(f"Database quota check failed: {e}", exc_info=e)
            # Fail open
            return True, {"allowed": True, "reason": "quota_check_failed"}

    def decrement_concurrent(self, tenant_id: int):
        """
        Decrement concurrent request counter.

        Call this after a request completes.

        Args:
            tenant_id: Tenant ID
        """
        if not self.redis_available:
            return

        try:
            key = self._get_concurrent_key(tenant_id)
            current = self.redis.get(key)

            if current and int(current) > 0:
                self.redis.decr(key)

        except Exception as e:
            logger.error(f"Failed to decrement concurrent counter: {e}", exc_info=e)

    def get_quota_status(self, tenant_id: int) -> Dict[str, Any]:
        """
        Get current quota status for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Quota status dictionary
        """
        try:
            # Get limits from database
            result = self.db_pool.execute_query(
                """
                SELECT api_calls_per_hour, api_calls_per_day, api_burst_limit
                FROM tenant_quotas
                WHERE tenant_id = %s
                """,
                (tenant_id,),
                fetch=True
            )

            if not result:
                return {"error": "No quotas found"}

            hourly_limit = result[0][0]
            daily_limit = result[0][1]
            burst_limit = result[0][2]

            if not self.redis_available:
                return {
                    "method": "database",
                    "redis_available": False,
                    "limits": {
                        "hourly": hourly_limit,
                        "daily": daily_limit,
                        "concurrent": burst_limit
                    }
                }

            # Get current counts from Redis
            hour_key = self._get_hour_key(tenant_id)
            day_key = self._get_day_key(tenant_id)
            concurrent_key = self._get_concurrent_key(tenant_id)

            pipe = self.redis.pipeline()
            pipe.get(hour_key)
            pipe.get(day_key)
            pipe.get(concurrent_key)
            pipe.ttl(hour_key)
            pipe.ttl(day_key)
            results = pipe.execute()

            hour_count = int(results[0]) if results[0] else 0
            day_count = int(results[1]) if results[1] else 0
            concurrent_count = int(results[2]) if results[2] else 0
            hour_ttl = results[3] if results[3] > 0 else 3600
            day_ttl = results[4] if results[4] > 0 else 86400

            return {
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
                "redis_available": True,
                "hourly": {
                    "current": hour_count,
                    "limit": hourly_limit,
                    "percent": round((hour_count / hourly_limit * 100), 2) if hourly_limit > 0 else 0,
                    "remaining": max(0, hourly_limit - hour_count),
                    "reset_in_seconds": hour_ttl
                },
                "daily": {
                    "current": day_count,
                    "limit": daily_limit,
                    "percent": round((day_count / daily_limit * 100), 2) if daily_limit > 0 else 0,
                    "remaining": max(0, daily_limit - day_count),
                    "reset_in_seconds": day_ttl
                },
                "concurrent": {
                    "current": concurrent_count,
                    "limit": burst_limit,
                    "remaining": max(0, burst_limit - concurrent_count)
                }
            }

        except Exception as e:
            logger.error(f"Failed to get quota status: {e}", exc_info=e)
            return {"error": str(e)}

    def reset_quota(self, tenant_id: int, quota_type: str = "all"):
        """
        Reset quota counters for a tenant (admin operation).

        Args:
            tenant_id: Tenant ID
            quota_type: Type to reset ('hourly', 'daily', 'concurrent', 'all')
        """
        if not self.redis_available:
            logger.warning("Cannot reset quota - Redis not available")
            return

        try:
            if quota_type in ["hourly", "all"]:
                self.redis.delete(self._get_hour_key(tenant_id))
                logger.info(f"Reset hourly quota for tenant {tenant_id}")

            if quota_type in ["daily", "all"]:
                self.redis.delete(self._get_day_key(tenant_id))
                logger.info(f"Reset daily quota for tenant {tenant_id}")

            if quota_type in ["concurrent", "all"]:
                self.redis.delete(self._get_concurrent_key(tenant_id))
                logger.info(f"Reset concurrent quota for tenant {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to reset quota: {e}", exc_info=e)

    def _get_hour_reset_time(self) -> str:
        """Get timestamp when hourly quota resets."""
        now = datetime.utcnow()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return next_hour.isoformat()

    def _get_day_reset_time(self) -> str:
        """Get timestamp when daily quota resets."""
        now = datetime.utcnow()
        next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return next_day.isoformat()

    def record_usage_history(self, tenant_id: int):
        """
        Record current usage to database for historical tracking.

        This should be called periodically (e.g., hourly) to maintain usage history.

        Args:
            tenant_id: Tenant ID
        """
        try:
            if not self.redis_available:
                return

            # Get current counts
            hour_key = self._get_hour_key(tenant_id)
            api_calls = int(self.redis.get(hour_key) or 0)

            if api_calls == 0:
                return  # Nothing to record

            # Record to database
            now = datetime.utcnow()
            period_start = now.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)

            self.db_pool.execute_query(
                """
                INSERT INTO tenant_usage (tenant_id, metric, value, period_start, period_end, created_at)
                VALUES (%s, 'api_calls', %s, %s, %s, NOW())
                ON CONFLICT DO NOTHING
                """,
                (tenant_id, api_calls, period_start, period_end),
                fetch=False
            )

            logger.debug(f"Recorded usage history for tenant {tenant_id}: {api_calls} API calls")

        except Exception as e:
            logger.error(f"Failed to record usage history: {e}", exc_info=e)

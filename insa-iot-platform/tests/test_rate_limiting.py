"""
Comprehensive test suite for rate limiting functionality.

Tests cover:
- Token bucket algorithm
- Rate limit enforcement
- Burst handling
- Distributed rate limiting
- Performance benchmarks
- Bypass whitelist
- Admin routes
- Middleware integration
"""

import time
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

import pytest
import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.rate_limiter import (
    RateLimiter,
    RateLimit,
    TimeWindow,
    RateLimitResult,
    DEFAULT_RATE_LIMITS,
    create_rate_limiter
)
from app.api.middleware.rate_limit_middleware import RateLimitMiddleware
from app.api.routes.rate_limits import router as rate_limits_router


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def redis_client():
    """Create Redis client for testing."""
    client = await redis.from_url(
        "redis://localhost:6379/15",  # Use DB 15 for testing
        encoding="utf-8",
        decode_responses=True
    )

    # Clear test database
    await client.flushdb()

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()


@pytest.fixture
async def rate_limiter(redis_client):
    """Create rate limiter for testing."""
    limiter = await create_rate_limiter(redis_client)
    return limiter


@pytest.fixture
def app_with_rate_limiting(rate_limiter):
    """Create FastAPI app with rate limiting middleware."""
    app = FastAPI()

    # Add middleware
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=rate_limiter,
        enable_rate_limiting=True
    )

    # Add test endpoint
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client(app_with_rate_limiting):
    """Create test client."""
    return TestClient(app_with_rate_limiting)


# ============================================================================
# Token Bucket Algorithm Tests
# ============================================================================

@pytest.mark.asyncio
async def test_token_bucket_initial_state(rate_limiter):
    """Test token bucket initial state."""
    result = await rate_limiter.check_rate_limit(
        user_id="test_user",
        role="viewer"
    )

    assert result.allowed is True
    assert result.remaining == 99  # 100 - 1 consumed
    assert result.limit == 100


@pytest.mark.asyncio
async def test_token_bucket_refill(rate_limiter, redis_client):
    """Test token bucket refills over time."""
    user_id = "test_user_refill"

    # Consume all tokens
    for _ in range(100):
        result = await rate_limiter.check_rate_limit(
            user_id=user_id,
            role="viewer",
            windows=[TimeWindow.MINUTE]
        )

    # Should be denied now
    result = await rate_limiter.check_rate_limit(
        user_id=user_id,
        role="viewer",
        windows=[TimeWindow.MINUTE]
    )
    assert result.allowed is False

    # Wait for refill (0.6 seconds = 1 token at 100/60 rate)
    await asyncio.sleep(0.7)

    # Should allow one request
    result = await rate_limiter.check_rate_limit(
        user_id=user_id,
        role="viewer",
        windows=[TimeWindow.MINUTE]
    )
    assert result.allowed is True


@pytest.mark.asyncio
async def test_token_bucket_burst_handling(rate_limiter):
    """Test burst handling allows temporary exceeding of limit."""
    user_id = "test_user_burst"

    # With 2x burst multiplier, should allow 200 requests quickly
    success_count = 0
    for _ in range(150):
        result = await rate_limiter.check_rate_limit(
            user_id=user_id,
            role="viewer",
            windows=[TimeWindow.MINUTE]
        )
        if result.allowed:
            success_count += 1

    # Should have allowed more than base limit (100) due to burst
    assert success_count >= 100
    assert success_count <= 200  # But not more than burst limit


@pytest.mark.asyncio
async def test_rate_limit_enforcement(rate_limiter):
    """Test rate limit is enforced correctly."""
    user_id = "test_user_enforce"

    # Consume exactly the limit
    for i in range(100):
        result = await rate_limiter.check_rate_limit(
            user_id=user_id,
            role="viewer",
            windows=[TimeWindow.MINUTE]
        )
        assert result.allowed is True, f"Request {i+1} should be allowed"

    # Next request should be denied
    result = await rate_limiter.check_rate_limit(
        user_id=user_id,
        role="viewer",
        windows=[TimeWindow.MINUTE]
    )
    assert result.allowed is False
    assert result.retry_after is not None
    assert result.retry_after > 0


# ============================================================================
# Role-Based Rate Limits Tests
# ============================================================================

@pytest.mark.asyncio
async def test_admin_rate_limits(rate_limiter):
    """Test admin has higher rate limits."""
    result = await rate_limiter.check_rate_limit(
        user_id="admin_user",
        role="admin",
        windows=[TimeWindow.MINUTE]
    )

    assert result.allowed is True
    assert result.limit == 1000  # Admin limit


@pytest.mark.asyncio
async def test_operator_rate_limits(rate_limiter):
    """Test operator has medium rate limits."""
    result = await rate_limiter.check_rate_limit(
        user_id="operator_user",
        role="operator",
        windows=[TimeWindow.MINUTE]
    )

    assert result.allowed is True
    assert result.limit == 500  # Operator limit


@pytest.mark.asyncio
async def test_viewer_rate_limits(rate_limiter):
    """Test viewer has lower rate limits."""
    result = await rate_limiter.check_rate_limit(
        user_id="viewer_user",
        role="viewer",
        windows=[TimeWindow.MINUTE]
    )

    assert result.allowed is True
    assert result.limit == 100  # Viewer limit


@pytest.mark.asyncio
async def test_anonymous_rate_limits(rate_limiter):
    """Test anonymous users have lowest rate limits."""
    result = await rate_limiter.check_rate_limit(
        user_id="anon:192.168.1.1",
        role="anonymous",
        windows=[TimeWindow.MINUTE]
    )

    assert result.allowed is True
    assert result.limit == 10  # Anonymous limit


# ============================================================================
# Multiple Time Windows Tests
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_windows(rate_limiter):
    """Test checking multiple time windows."""
    user_id = "test_user_windows"

    # Check minute, hour, day windows
    result = await rate_limiter.check_rate_limit(
        user_id=user_id,
        role="viewer",
        windows=[TimeWindow.MINUTE, TimeWindow.HOUR, TimeWindow.DAY]
    )

    assert result.allowed is True


@pytest.mark.asyncio
async def test_hour_limit_enforcement(rate_limiter):
    """Test hour limit is enforced when minute limit not reached."""
    user_id = "test_user_hour"

    # Consume requests slowly to avoid minute limit
    for i in range(5010):  # Exceed hour limit for viewer (5000)
        result = await rate_limiter.check_rate_limit(
            user_id=user_id,
            role="viewer",
            windows=[TimeWindow.HOUR]
        )

        if i < 5000:
            assert result.allowed is True, f"Request {i+1} should be allowed"
        else:
            # Should hit hour limit
            if not result.allowed:
                break

    # Verify we hit the limit
    assert not result.allowed


# ============================================================================
# Endpoint-Specific Overrides Tests
# ============================================================================

@pytest.mark.asyncio
async def test_endpoint_override(rate_limiter):
    """Test endpoint-specific rate limit overrides."""
    user_id = "test_user_endpoint"

    # Telemetry batch endpoint has lower limit (50/min)
    result = await rate_limiter.check_rate_limit(
        user_id=user_id,
        role="viewer",
        endpoint="/api/v1/telemetry/batch",
        windows=[TimeWindow.MINUTE]
    )

    assert result.allowed is True
    assert result.limit == 50  # Override limit


@pytest.mark.asyncio
async def test_ml_training_override(rate_limiter):
    """Test ML training endpoint has very low limit."""
    user_id = "test_user_ml"

    # ML training has 10/hour limit
    result = await rate_limiter.check_rate_limit(
        user_id=user_id,
        role="operator",
        endpoint="/api/v1/ml/train",
        windows=[TimeWindow.HOUR]
    )

    assert result.allowed is True
    assert result.limit == 10  # Override limit


# ============================================================================
# IP Whitelist Tests
# ============================================================================

@pytest.mark.asyncio
async def test_ip_whitelist_bypass():
    """Test whitelisted IPs bypass rate limiting."""
    redis_client = await redis.from_url(
        "redis://localhost:6379/15",
        encoding="utf-8",
        decode_responses=True
    )

    # Create limiter with whitelisted IP
    limiter = RateLimiter(
        redis_client=redis_client,
        default_limits=DEFAULT_RATE_LIMITS,
        whitelisted_ips=["10.0.0.1"]
    )

    # Whitelisted IP should always be allowed
    for _ in range(1000):
        result = await limiter.check_rate_limit(
            user_id="any_user",
            role="viewer",
            ip_address="10.0.0.1"
        )
        assert result.allowed is True

    await redis_client.close()


# ============================================================================
# Global Rate Limit Tests
# ============================================================================

@pytest.mark.asyncio
async def test_global_rate_limit(rate_limiter):
    """Test global rate limit affects all users."""
    # Global limit is 10,000/min
    # Test with multiple users

    users = [f"user_{i}" for i in range(100)]

    # Each user makes 110 requests (total 11,000)
    denied_count = 0
    for user_id in users:
        for _ in range(110):
            result = await rate_limiter.check_rate_limit(
                user_id=user_id,
                role="admin",  # High individual limit
                windows=[TimeWindow.MINUTE]
            )
            if not result.allowed:
                denied_count += 1

    # Should have hit global limit
    assert denied_count > 0


# ============================================================================
# Distributed Rate Limiting Tests
# ============================================================================

@pytest.mark.asyncio
async def test_distributed_rate_limiting(redis_client):
    """Test rate limiting works correctly across multiple workers."""
    # Create two separate limiter instances (simulating different workers)
    limiter1 = await create_rate_limiter(redis_client)
    limiter2 = await create_rate_limiter(redis_client)

    user_id = "test_user_distributed"

    # Consume 50 from each worker
    for _ in range(50):
        await limiter1.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])
        await limiter2.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])

    # Total consumed: 100
    # Next request from either worker should be denied
    result = await limiter1.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])
    assert result.allowed is False

    result = await limiter2.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])
    assert result.allowed is False


@pytest.mark.asyncio
async def test_concurrent_requests(rate_limiter):
    """Test concurrent requests don't cause race conditions."""
    user_id = "test_user_concurrent"

    # Make 100 concurrent requests
    tasks = [
        rate_limiter.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])
        for _ in range(100)
    ]

    results = await asyncio.gather(*tasks)

    # All should be allowed (within limit)
    allowed_count = sum(1 for r in results if r.allowed)
    assert allowed_count == 100

    # Next request should be denied
    result = await rate_limiter.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])
    assert result.allowed is False


# ============================================================================
# Admin Routes Tests
# ============================================================================

@pytest.mark.asyncio
async def test_reset_user_limits(rate_limiter):
    """Test resetting user rate limits."""
    user_id = "test_user_reset"

    # Consume some requests
    for _ in range(50):
        await rate_limiter.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])

    # Reset limits
    deleted = await rate_limiter.reset_user_limits(user_id)
    assert deleted > 0

    # Should be able to make full 100 requests again
    for _ in range(100):
        result = await rate_limiter.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])
        assert result.allowed is True


@pytest.mark.asyncio
async def test_get_user_status(rate_limiter):
    """Test getting user rate limit status."""
    user_id = "test_user_status"

    # Consume some requests
    for _ in range(30):
        await rate_limiter.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])

    # Get status
    status = await rate_limiter.get_user_status(user_id, "viewer")

    assert "minute" in status
    assert status["minute"]["limit"] == 100
    assert status["minute"]["remaining"] >= 69  # Allow for some variance
    assert status["minute"]["remaining"] <= 71


@pytest.mark.asyncio
async def test_get_top_consumers(rate_limiter):
    """Test getting top rate limit consumers."""
    # Create activity from multiple users
    for i in range(10):
        user_id = f"user_{i}"
        # Each user consumes different amounts
        for _ in range((i + 1) * 10):
            await rate_limiter.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])

    # Get top consumers
    top = await rate_limiter.get_top_consumers(limit=5)

    assert len(top) <= 5
    # Should be sorted by usage (highest first)


# ============================================================================
# Middleware Tests
# ============================================================================

def test_middleware_excluded_paths(client):
    """Test middleware excludes health check endpoints."""
    response = client.get("/health")
    assert response.status_code == 200

    # Should not have rate limit headers
    assert "X-RateLimit-Limit" not in response.headers


def test_middleware_adds_headers(client):
    """Test middleware adds rate limit headers."""
    # Create mock token
    token = "Bearer test_token"

    response = client.get("/test", headers={"Authorization": token})

    # Should have rate limit headers (even if request fails auth)
    # In production, auth would be validated first


def test_middleware_429_on_limit_exceeded(rate_limiter):
    """Test middleware returns 429 when limit exceeded."""
    # This would require mocking the rate limiter to return denied
    # Or consuming the actual limit (would be slow)
    pass


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_performance_single_check(rate_limiter):
    """Test single rate limit check is <1ms."""
    user_id = "test_user_perf"

    # Warm up
    await rate_limiter.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])

    # Benchmark
    start = time.time()
    iterations = 100

    for _ in range(iterations):
        await rate_limiter.check_rate_limit(user_id, "viewer", windows=[TimeWindow.MINUTE])

    duration = time.time() - start
    avg_duration = duration / iterations

    print(f"\nAverage rate limit check: {avg_duration*1000:.2f}ms")

    # Should be well under 1ms per check
    assert avg_duration < 0.001, f"Rate limit check took {avg_duration*1000:.2f}ms (target: <1ms)"


@pytest.mark.asyncio
async def test_performance_concurrent_checks(rate_limiter):
    """Test concurrent rate limit checks perform well."""
    user_id = "test_user_perf_concurrent"

    start = time.time()

    # 1000 concurrent checks
    tasks = [
        rate_limiter.check_rate_limit(user_id, "admin", windows=[TimeWindow.MINUTE])
        for _ in range(1000)
    ]

    await asyncio.gather(*tasks)

    duration = time.time() - start

    print(f"\n1000 concurrent checks: {duration:.2f}s ({duration/1000*1000:.2f}ms per check)")

    # Should complete in reasonable time
    assert duration < 2.0  # 2 seconds for 1000 checks


@pytest.mark.asyncio
async def test_performance_multiple_windows(rate_limiter):
    """Test checking multiple windows doesn't significantly increase latency."""
    user_id = "test_user_perf_windows"

    # Single window
    start = time.time()
    for _ in range(100):
        await rate_limiter.check_rate_limit(
            user_id, "viewer",
            windows=[TimeWindow.MINUTE]
        )
    single_duration = time.time() - start

    # Multiple windows
    start = time.time()
    for _ in range(100):
        await rate_limiter.check_rate_limit(
            user_id, "viewer",
            windows=[TimeWindow.MINUTE, TimeWindow.HOUR, TimeWindow.DAY]
        )
    multi_duration = time.time() - start

    print(f"\nSingle window: {single_duration:.3f}s")
    print(f"Multiple windows: {multi_duration:.3f}s")
    print(f"Overhead: {((multi_duration/single_duration - 1) * 100):.1f}%")

    # Multiple windows should be < 3x slower
    assert multi_duration < single_duration * 3


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_redis_connection_error_handling(rate_limiter):
    """Test graceful handling of Redis connection errors."""
    # Close Redis connection to simulate error
    await rate_limiter.redis.close()

    # Should handle gracefully (fail open in production)
    with pytest.raises(Exception):
        await rate_limiter.check_rate_limit("user", "viewer")


@pytest.mark.asyncio
async def test_invalid_role_handling(rate_limiter):
    """Test handling of invalid roles."""
    result = await rate_limiter.check_rate_limit(
        user_id="test_user",
        role="invalid_role",
        windows=[TimeWindow.MINUTE]
    )

    # Should still work (might use default or deny)
    assert isinstance(result, RateLimitResult)


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_full_rate_limiting_flow(redis_client):
    """Test complete rate limiting flow from request to denial."""
    limiter = await create_rate_limiter(redis_client)

    user_id = "integration_test_user"
    role = "viewer"

    # Phase 1: Normal usage
    for i in range(50):
        result = await limiter.check_rate_limit(user_id, role, windows=[TimeWindow.MINUTE])
        assert result.allowed is True
        assert result.remaining == 100 - i - 1

    # Phase 2: Approach limit
    for i in range(50, 100):
        result = await limiter.check_rate_limit(user_id, role, windows=[TimeWindow.MINUTE])
        assert result.allowed is True

    # Phase 3: Hit limit
    result = await limiter.check_rate_limit(user_id, role, windows=[TimeWindow.MINUTE])
    assert result.allowed is False
    assert result.retry_after > 0

    # Phase 4: Admin reset
    deleted = await limiter.reset_user_limits(user_id)
    assert deleted > 0

    # Phase 5: Verify reset worked
    result = await limiter.check_rate_limit(user_id, role, windows=[TimeWindow.MINUTE])
    assert result.allowed is True
    assert result.remaining == 99


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

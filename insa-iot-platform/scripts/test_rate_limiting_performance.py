#!/usr/bin/env python3
"""
Performance test script for rate limiting implementation.

Tests:
- Single check latency
- Concurrent check throughput
- Multi-window check overhead
- Memory usage

Target: <1ms per check
"""

import asyncio
import time
import statistics
from typing import List

import redis.asyncio as redis

from app.core.rate_limiter import create_rate_limiter, TimeWindow


async def test_single_check_latency(iterations: int = 1000):
    """Test single rate limit check latency."""
    print("\n" + "="*60)
    print("Test 1: Single Check Latency")
    print("="*60)

    # Setup
    redis_client = await redis.from_url(
        "redis://localhost:6379/15",
        encoding="utf-8",
        decode_responses=True
    )
    await redis_client.flushdb()

    limiter = await create_rate_limiter(redis_client)

    # Warm up
    for _ in range(10):
        await limiter.check_rate_limit("warmup", "viewer", windows=[TimeWindow.MINUTE])

    # Benchmark
    latencies = []
    for i in range(iterations):
        start = time.perf_counter()
        await limiter.check_rate_limit(f"user_{i}", "viewer", windows=[TimeWindow.MINUTE])
        latency = time.perf_counter() - start
        latencies.append(latency * 1000)  # Convert to ms

    # Results
    avg_latency = statistics.mean(latencies)
    p50_latency = statistics.median(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
    p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
    max_latency = max(latencies)

    print(f"\nIterations: {iterations}")
    print(f"Average:    {avg_latency:.3f}ms")
    print(f"P50:        {p50_latency:.3f}ms")
    print(f"P95:        {p95_latency:.3f}ms")
    print(f"P99:        {p99_latency:.3f}ms")
    print(f"Max:        {max_latency:.3f}ms")

    # Verdict
    if p99_latency < 1.0:
        print(f"\n✅ PASS: P99 latency ({p99_latency:.3f}ms) < 1ms target")
    else:
        print(f"\n❌ FAIL: P99 latency ({p99_latency:.3f}ms) >= 1ms target")

    await redis_client.close()

    return p99_latency < 1.0


async def test_concurrent_throughput(concurrent_users: int = 100, requests_per_user: int = 10):
    """Test concurrent request throughput."""
    print("\n" + "="*60)
    print("Test 2: Concurrent Throughput")
    print("="*60)

    # Setup
    redis_client = await redis.from_url(
        "redis://localhost:6379/15",
        encoding="utf-8",
        decode_responses=True
    )
    await redis_client.flushdb()

    limiter = await create_rate_limiter(redis_client)

    # Benchmark
    total_requests = concurrent_users * requests_per_user

    async def user_workload(user_id: int):
        for _ in range(requests_per_user):
            await limiter.check_rate_limit(f"user_{user_id}", "admin", windows=[TimeWindow.MINUTE])

    start = time.perf_counter()
    tasks = [user_workload(i) for i in range(concurrent_users)]
    await asyncio.gather(*tasks)
    duration = time.perf_counter() - start

    # Results
    throughput = total_requests / duration

    print(f"\nConcurrent users:  {concurrent_users}")
    print(f"Requests per user: {requests_per_user}")
    print(f"Total requests:    {total_requests}")
    print(f"Duration:          {duration:.2f}s")
    print(f"Throughput:        {throughput:.0f} req/s")
    print(f"Avg latency:       {duration/total_requests*1000:.3f}ms")

    # Verdict
    target_throughput = 2500  # 2500 req/s per core
    if throughput >= target_throughput:
        print(f"\n✅ PASS: Throughput ({throughput:.0f} req/s) >= {target_throughput} req/s target")
    else:
        print(f"\n⚠️  WARNING: Throughput ({throughput:.0f} req/s) < {target_throughput} req/s target")

    await redis_client.close()

    return throughput >= target_throughput


async def test_multi_window_overhead(iterations: int = 100):
    """Test overhead of checking multiple time windows."""
    print("\n" + "="*60)
    print("Test 3: Multi-Window Overhead")
    print("="*60)

    # Setup
    redis_client = await redis.from_url(
        "redis://localhost:6379/15",
        encoding="utf-8",
        decode_responses=True
    )
    await redis_client.flushdb()

    limiter = await create_rate_limiter(redis_client)

    # Test single window
    start = time.perf_counter()
    for i in range(iterations):
        await limiter.check_rate_limit(
            f"user_single_{i}",
            "viewer",
            windows=[TimeWindow.MINUTE]
        )
    single_duration = time.perf_counter() - start

    # Test multiple windows
    start = time.perf_counter()
    for i in range(iterations):
        await limiter.check_rate_limit(
            f"user_multi_{i}",
            "viewer",
            windows=[TimeWindow.MINUTE, TimeWindow.HOUR, TimeWindow.DAY]
        )
    multi_duration = time.perf_counter() - start

    # Results
    single_avg = single_duration / iterations * 1000
    multi_avg = multi_duration / iterations * 1000
    overhead_percent = ((multi_duration / single_duration) - 1) * 100

    print(f"\nIterations:       {iterations}")
    print(f"Single window:    {single_avg:.3f}ms per check")
    print(f"Multi-window (3): {multi_avg:.3f}ms per check")
    print(f"Overhead:         {overhead_percent:.1f}%")
    print(f"Multiplier:       {multi_duration/single_duration:.2f}x")

    # Verdict
    if multi_duration < single_duration * 3:
        print(f"\n✅ PASS: Multi-window overhead ({overhead_percent:.1f}%) is acceptable")
    else:
        print(f"\n❌ FAIL: Multi-window overhead ({overhead_percent:.1f}%) is too high")

    await redis_client.close()

    return multi_duration < single_duration * 3


async def test_distributed_consistency(workers: int = 5, requests_per_worker: int = 20):
    """Test rate limiting consistency across multiple workers."""
    print("\n" + "="*60)
    print("Test 4: Distributed Consistency")
    print("="*60)

    # Setup
    redis_client = await redis.from_url(
        "redis://localhost:6379/15",
        encoding="utf-8",
        decode_responses=True
    )
    await redis_client.flushdb()

    # Create multiple limiter instances (simulating different workers)
    limiters = [await create_rate_limiter(redis_client) for _ in range(workers)]

    user_id = "distributed_test_user"
    role = "viewer"  # 100 req/min limit

    # Each worker makes requests
    async def worker_requests(worker_id: int):
        limiter = limiters[worker_id]
        allowed = 0
        denied = 0

        for _ in range(requests_per_worker):
            result = await limiter.check_rate_limit(
                user_id,
                role,
                windows=[TimeWindow.MINUTE]
            )
            if result.allowed:
                allowed += 1
            else:
                denied += 1

        return allowed, denied

    # Run all workers concurrently
    results = await asyncio.gather(*[worker_requests(i) for i in range(workers)])

    # Calculate totals
    total_allowed = sum(r[0] for r in results)
    total_denied = sum(r[1] for r in results)
    total_requests = total_allowed + total_denied

    print(f"\nWorkers:          {workers}")
    print(f"Requests/worker:  {requests_per_worker}")
    print(f"Total requests:   {total_requests}")
    print(f"Allowed:          {total_allowed}")
    print(f"Denied:           {total_denied}")
    print(f"Expected allowed: 100 (rate limit)")

    # Verdict
    # Should allow exactly 100 requests (the limit)
    if 98 <= total_allowed <= 102:  # Allow 2% variance
        print(f"\n✅ PASS: Distributed rate limiting is consistent")
    else:
        print(f"\n❌ FAIL: Expected ~100 allowed, got {total_allowed}")

    await redis_client.close()

    return 98 <= total_allowed <= 102


async def test_memory_efficiency():
    """Test memory footprint of rate limiting."""
    print("\n" + "="*60)
    print("Test 5: Memory Efficiency")
    print("="*60)

    # Setup
    redis_client = await redis.from_url(
        "redis://localhost:6379/15",
        encoding="utf-8",
        decode_responses=True
    )
    await redis_client.flushdb()

    limiter = await create_rate_limiter(redis_client)

    # Create rate limit entries for many users
    num_users = 1000
    print(f"\nCreating rate limit entries for {num_users} users...")

    for i in range(num_users):
        await limiter.check_rate_limit(
            f"user_{i}",
            "viewer",
            windows=[TimeWindow.MINUTE, TimeWindow.HOUR, TimeWindow.DAY]
        )

    # Check Redis memory usage
    info = await redis_client.info("memory")
    used_memory_mb = info["used_memory"] / (1024 * 1024)
    bytes_per_user = info["used_memory"] / num_users

    print(f"\nUsers:              {num_users}")
    print(f"Total memory:       {used_memory_mb:.2f} MB")
    print(f"Bytes per user:     {bytes_per_user:.0f} bytes")
    print(f"Memory per 1M users: {bytes_per_user * 1000000 / (1024*1024):.2f} MB")

    # Verdict
    target_bytes_per_user = 500  # Target: <500 bytes per user
    if bytes_per_user <= target_bytes_per_user:
        print(f"\n✅ PASS: Memory usage ({bytes_per_user:.0f} bytes/user) is efficient")
    else:
        print(f"\n⚠️  WARNING: Memory usage ({bytes_per_user:.0f} bytes/user) > {target_bytes_per_user} bytes/user")

    await redis_client.close()

    return bytes_per_user <= target_bytes_per_user


async def main():
    """Run all performance tests."""
    print("\n" + "="*60)
    print("RATE LIMITING PERFORMANCE TEST SUITE")
    print("="*60)
    print("\nTarget: <1ms per check, 2500+ req/s throughput")

    results = {}

    try:
        results["latency"] = await test_single_check_latency(iterations=1000)
        results["throughput"] = await test_concurrent_throughput(concurrent_users=100, requests_per_user=10)
        results["multi_window"] = await test_multi_window_overhead(iterations=100)
        results["distributed"] = await test_distributed_consistency(workers=5, requests_per_worker=20)
        results["memory"] = await test_memory_efficiency()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Final summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():20} {status}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Production ready!")
    else:
        print("❌ SOME TESTS FAILED - Review and optimize")
    print("="*60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

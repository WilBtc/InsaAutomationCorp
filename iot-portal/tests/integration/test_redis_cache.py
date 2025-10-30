#!/usr/bin/env python3
"""
Integration Tests for Redis Cache Layer
INSA Advanced IIoT Platform v2.0
Updated: October 28, 2025

Tests the Redis caching system:
- Cache hit/miss tracking
- TTL management
- Invalidation strategies
- Performance optimization
"""

import pytest
import json
import time
from datetime import datetime, timedelta
import redis


@pytest.mark.integration
@pytest.mark.cache
class TestRedisCacheBasics:
    """Basic Redis cache functionality tests"""

    def test_cache_connection(self, redis_client):
        """Test Redis connection"""
        assert redis_client.ping() is True

    def test_cache_set_get(self, redis_client):
        """Test basic cache set/get operations"""
        key = 'test:key:1'
        value = {'data': 'test value', 'timestamp': datetime.now().isoformat()}

        # Set value
        redis_client.set(key, json.dumps(value), ex=60)

        # Get value
        cached = redis_client.get(key)
        assert cached is not None

        retrieved = json.loads(cached)
        assert retrieved['data'] == 'test value'

    def test_cache_expiration(self, redis_client):
        """Test cache TTL expiration"""
        key = 'test:expiring:key'
        value = 'test value'

        # Set with 2 second TTL
        redis_client.set(key, value, ex=2)

        # Should exist immediately
        assert redis_client.get(key) == value

        # Wait for expiration
        time.sleep(3)

        # Should be gone
        assert redis_client.get(key) is None

    def test_cache_delete(self, redis_client):
        """Test cache deletion"""
        key = 'test:delete:key'
        redis_client.set(key, 'value')

        # Verify exists
        assert redis_client.exists(key) == 1

        # Delete
        redis_client.delete(key)

        # Verify gone
        assert redis_client.exists(key) == 0

    def test_cache_multiple_keys(self, redis_client):
        """Test caching multiple keys"""
        keys_values = {
            'test:key:1': 'value1',
            'test:key:2': 'value2',
            'test:key:3': 'value3'
        }

        # Set multiple keys
        for key, value in keys_values.items():
            redis_client.set(key, value)

        # Get all keys
        for key, expected_value in keys_values.items():
            assert redis_client.get(key) == expected_value

        # Clean up
        redis_client.delete(*keys_values.keys())


@pytest.mark.integration
@pytest.mark.cache
class TestRedisCachePatterns:
    """Test cache patterns and strategies"""

    def test_cache_pattern_matching(self, redis_client):
        """Test pattern-based key retrieval"""
        # Set multiple keys with pattern
        for i in range(5):
            redis_client.set(f'device:DEVICE-{i}:temperature', 20.0 + i)

        # Get all temperature keys
        keys = redis_client.keys('device:*:temperature')

        assert len(keys) >= 5

        # Clean up
        if keys:
            redis_client.delete(*keys)

    def test_cache_hash_operations(self, redis_client):
        """Test Redis hash operations for structured data"""
        hash_key = 'device:DEVICE-001:metrics'

        # Set hash fields
        redis_client.hset(hash_key, mapping={
            'temperature': '25.5',
            'pressure': '101.3',
            'humidity': '65.0'
        })

        # Get specific field
        temp = redis_client.hget(hash_key, 'temperature')
        assert temp == '25.5'

        # Get all fields
        all_metrics = redis_client.hgetall(hash_key)
        assert len(all_metrics) == 3

        # Clean up
        redis_client.delete(hash_key)

    def test_cache_list_operations(self, redis_client):
        """Test Redis list operations for time-series data"""
        list_key = 'telemetry:DEVICE-001:temperature'

        # Push values
        for i in range(10):
            redis_client.rpush(list_key, json.dumps({
                'value': 20.0 + i,
                'timestamp': (datetime.now() - timedelta(minutes=10-i)).isoformat()
            }))

        # Get list length
        length = redis_client.llen(list_key)
        assert length == 10

        # Get range
        recent_5 = redis_client.lrange(list_key, -5, -1)
        assert len(recent_5) == 5

        # Clean up
        redis_client.delete(list_key)

    def test_cache_sorted_set(self, redis_client):
        """Test Redis sorted set for time-ordered data"""
        sorted_key = 'alerts:priority'

        # Add alerts with priority scores
        redis_client.zadd(sorted_key, {
            'alert:1': 10,  # Low priority
            'alert:2': 50,  # Medium priority
            'alert:3': 90   # High priority
        })

        # Get highest priority alerts
        high_priority = redis_client.zrevrange(sorted_key, 0, 1)
        assert high_priority[0] == 'alert:3'

        # Get by score range
        medium_to_high = redis_client.zrangebyscore(sorted_key, 50, 100)
        assert len(medium_to_high) == 2

        # Clean up
        redis_client.delete(sorted_key)


@pytest.mark.integration
@pytest.mark.cache
class TestCachePerformance:
    """Test cache performance and optimization"""

    def test_cache_hit_rate_tracking(self, redis_client):
        """Test cache hit/miss tracking"""
        # Simulate cache hits and misses
        hits = 0
        misses = 0

        for i in range(100):
            key = f'test:perf:key:{i % 10}'  # Reuse 10 keys

            if redis_client.exists(key):
                hits += 1
                redis_client.get(key)
            else:
                misses += 1
                redis_client.set(key, f'value-{i}', ex=60)

        # Should have some hits due to key reuse
        hit_rate = hits / (hits + misses)
        assert hit_rate > 0

        # Clean up
        for i in range(10):
            redis_client.delete(f'test:perf:key:{i}')

    @pytest.mark.slow
    def test_cache_bulk_operations(self, redis_client):
        """Test bulk cache operations performance"""
        import time

        # Test bulk write
        start = time.time()
        pipe = redis_client.pipeline()

        for i in range(1000):
            pipe.set(f'bulk:key:{i}', f'value-{i}')

        pipe.execute()
        write_time = time.time() - start

        # Should be fast (<1 second for 1000 keys)
        assert write_time < 1.0

        # Test bulk read
        start = time.time()
        pipe = redis_client.pipeline()

        for i in range(1000):
            pipe.get(f'bulk:key:{i}')

        values = pipe.execute()
        read_time = time.time() - start

        assert len(values) == 1000
        assert read_time < 1.0

        # Clean up
        pipe = redis_client.pipeline()
        for i in range(1000):
            pipe.delete(f'bulk:key:{i}')
        pipe.execute()

    def test_cache_memory_efficiency(self, redis_client):
        """Test cache memory usage"""
        # Store 100 small JSON objects
        for i in range(100):
            key = f'mem:test:{i}'
            value = json.dumps({
                'id': i,
                'value': 25.5,
                'timestamp': datetime.now().isoformat()
            })
            redis_client.set(key, value, ex=300)

        # Get memory info
        info = redis_client.info('memory')

        # Should have some memory usage
        assert info['used_memory'] > 0

        # Clean up
        for i in range(100):
            redis_client.delete(f'mem:test:{i}')


@pytest.mark.integration
@pytest.mark.cache
class TestCacheIntegrationWithApp:
    """Test cache integration with application"""

    def test_cache_device_query_results(self, redis_client):
        """Test caching database query results"""
        cache_key = 'query:devices:all'

        # Simulate cached query result
        devices = [
            {'id': 'DEVICE-001', 'name': 'Sensor 1'},
            {'id': 'DEVICE-002', 'name': 'Sensor 2'}
        ]

        redis_client.set(cache_key, json.dumps(devices), ex=300)

        # Retrieve from cache
        cached = redis_client.get(cache_key)
        retrieved_devices = json.loads(cached)

        assert len(retrieved_devices) == 2
        assert retrieved_devices[0]['id'] == 'DEVICE-001'

        # Clean up
        redis_client.delete(cache_key)

    def test_cache_telemetry_aggregation(self, redis_client):
        """Test caching aggregated telemetry data"""
        cache_key = 'agg:DEVICE-001:temperature:hourly'

        # Cache hourly average
        aggregation = {
            'device_id': 'DEVICE-001',
            'metric': 'temperature',
            'period': 'hourly',
            'avg': 25.5,
            'min': 20.0,
            'max': 30.0,
            'count': 3600
        }

        redis_client.set(cache_key, json.dumps(aggregation), ex=3600)

        # Retrieve aggregation
        cached = redis_client.get(cache_key)
        retrieved = json.loads(cached)

        assert retrieved['avg'] == 25.5
        assert retrieved['count'] == 3600

        # Clean up
        redis_client.delete(cache_key)

    def test_cache_invalidation_on_update(self, redis_client):
        """Test cache invalidation when data changes"""
        device_cache_key = 'device:DEVICE-001'

        # Set initial cache
        redis_client.set(device_cache_key, json.dumps({
            'id': 'DEVICE-001',
            'status': 'active'
        }), ex=300)

        # Simulate device update - invalidate cache
        redis_client.delete(device_cache_key)

        # Cache should be gone
        assert redis_client.get(device_cache_key) is None

    def test_cache_rule_evaluation_results(self, redis_client):
        """Test caching rule evaluation results"""
        cache_key = 'rules:eval:DEVICE-001:last'

        # Cache last evaluation result
        evaluation = {
            'timestamp': datetime.now().isoformat(),
            'rules_triggered': ['rule-1', 'rule-3'],
            'alerts_generated': 2
        }

        redis_client.set(cache_key, json.dumps(evaluation), ex=30)

        # Retrieve result
        cached = redis_client.get(cache_key)
        retrieved = json.loads(cached)

        assert len(retrieved['rules_triggered']) == 2

        # Clean up
        redis_client.delete(cache_key)

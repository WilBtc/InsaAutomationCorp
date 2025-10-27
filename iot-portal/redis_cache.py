#!/usr/bin/env python3
"""
Redis Cache Manager for INSA Advanced IIoT Platform v2.0
Phase 2 - Feature 6

Provides intelligent caching layer for:
- Device information and status
- Recent telemetry data
- Active rules (avoid DB queries every evaluation)
- Alert history
- Statistical aggregations

Cache Strategy:
- Write-through: Update cache on write
- TTL-based expiration: Different TTLs for different data types
- LRU eviction: Automatic memory management
- Cache invalidation: On data updates/deletes

Author: INSA Automation Corp
Date: October 27, 2025
"""

import redis
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based caching layer with intelligent TTL management
    """

    # Cache TTL configurations (in seconds)
    TTL_DEVICE_INFO = 300  # 5 minutes - device data changes infrequently
    TTL_TELEMETRY = 60  # 1 minute - telemetry data changes frequently
    TTL_RULES = 600  # 10 minutes - rules change rarely
    TTL_ALERTS = 180  # 3 minutes - alerts are time-sensitive
    TTL_STATS = 120  # 2 minutes - statistical aggregations

    def __init__(self, config: Dict):
        """
        Initialize Redis cache connection

        Args:
            config: Redis configuration
                {
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0,
                    'password': None,
                    'decode_responses': True,
                    'socket_timeout': 5,
                    'max_connections': 50
                }
        """
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 6379)
        self.db = config.get('db', 0)
        self.password = config.get('password')

        # Connection pool for better performance
        pool_config = {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'password': self.password,
            'decode_responses': True,
            'socket_timeout': config.get('socket_timeout', 5),
            'max_connections': config.get('max_connections', 50)
        }

        self.pool = redis.ConnectionPool(**pool_config)
        self.client = redis.Redis(connection_pool=self.pool)

        logger.info(f"Redis cache initialized - {self.host}:{self.port}/{self.db}")

    def test_connection(self) -> bool:
        """
        Test Redis connection

        Returns:
            bool: True if connection successful
        """
        try:
            self.client.ping()
            logger.info("Redis connection test successful")
            return True
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False

    # ============================================================================
    # DEVICE CACHING
    # ============================================================================

    def cache_device(self, device_id: str, device_data: Dict) -> bool:
        """
        Cache device information

        Args:
            device_id: Device ID
            device_data: Device data dictionary

        Returns:
            bool: True if cached successfully
        """
        try:
            key = f"device:{device_id}"
            value = json.dumps(device_data, default=str)
            self.client.setex(key, self.TTL_DEVICE_INFO, value)
            return True
        except Exception as e:
            logger.error(f"Error caching device {device_id}: {e}")
            return False

    def get_device(self, device_id: str) -> Optional[Dict]:
        """
        Get device from cache

        Args:
            device_id: Device ID

        Returns:
            Device data or None if not cached
        """
        try:
            key = f"device:{device_id}"
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting device {device_id} from cache: {e}")
            return None

    def invalidate_device(self, device_id: str) -> bool:
        """
        Invalidate device cache

        Args:
            device_id: Device ID

        Returns:
            bool: True if invalidated successfully
        """
        try:
            key = f"device:{device_id}"
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating device {device_id}: {e}")
            return False

    # ============================================================================
    # TELEMETRY CACHING
    # ============================================================================

    def cache_telemetry(self, device_id: str, key: str, value: Any, timestamp: datetime) -> bool:
        """
        Cache latest telemetry reading

        Args:
            device_id: Device ID
            key: Telemetry key (e.g., "temperature")
            value: Telemetry value
            timestamp: Reading timestamp

        Returns:
            bool: True if cached successfully
        """
        try:
            cache_key = f"telemetry:{device_id}:{key}"
            data = {
                'value': value,
                'timestamp': timestamp.isoformat()
            }
            value_str = json.dumps(data, default=str)
            self.client.setex(cache_key, self.TTL_TELEMETRY, value_str)
            return True
        except Exception as e:
            logger.error(f"Error caching telemetry {device_id}/{key}: {e}")
            return False

    def get_telemetry(self, device_id: str, key: str) -> Optional[Dict]:
        """
        Get latest telemetry reading from cache

        Args:
            device_id: Device ID
            key: Telemetry key

        Returns:
            Telemetry data with value and timestamp, or None
        """
        try:
            cache_key = f"telemetry:{device_id}:{key}"
            value = self.client.get(cache_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting telemetry {device_id}/{key}: {e}")
            return None

    def cache_telemetry_batch(self, device_id: str, telemetry_dict: Dict[str, Any], timestamp: datetime) -> bool:
        """
        Cache multiple telemetry readings at once

        Args:
            device_id: Device ID
            telemetry_dict: Dictionary of key-value pairs
            timestamp: Reading timestamp

        Returns:
            bool: True if all cached successfully
        """
        try:
            pipe = self.client.pipeline()
            for key, value in telemetry_dict.items():
                cache_key = f"telemetry:{device_id}:{key}"
                data = {
                    'value': value,
                    'timestamp': timestamp.isoformat()
                }
                value_str = json.dumps(data, default=str)
                pipe.setex(cache_key, self.TTL_TELEMETRY, value_str)
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Error caching telemetry batch for {device_id}: {e}")
            return False

    # ============================================================================
    # RULE CACHING
    # ============================================================================

    def cache_rules(self, rules: List[Dict]) -> bool:
        """
        Cache all active rules

        Args:
            rules: List of rule dictionaries

        Returns:
            bool: True if cached successfully
        """
        try:
            key = "rules:active"
            value = json.dumps(rules, default=str)
            self.client.setex(key, self.TTL_RULES, value)
            logger.debug(f"Cached {len(rules)} active rules")
            return True
        except Exception as e:
            logger.error(f"Error caching rules: {e}")
            return False

    def get_rules(self) -> Optional[List[Dict]]:
        """
        Get active rules from cache

        Returns:
            List of rule dictionaries or None
        """
        try:
            key = "rules:active"
            value = self.client.get(key)
            if value:
                rules = json.loads(value)
                logger.debug(f"Retrieved {len(rules)} rules from cache")
                return rules
            return None
        except Exception as e:
            logger.error(f"Error getting rules from cache: {e}")
            return None

    def invalidate_rules(self) -> bool:
        """
        Invalidate rules cache (call when rules are modified)

        Returns:
            bool: True if invalidated successfully
        """
        try:
            key = "rules:active"
            self.client.delete(key)
            logger.debug("Rules cache invalidated")
            return True
        except Exception as e:
            logger.error(f"Error invalidating rules cache: {e}")
            return False

    # ============================================================================
    # ALERT CACHING
    # ============================================================================

    def cache_recent_alerts(self, device_id: str, alerts: List[Dict]) -> bool:
        """
        Cache recent alerts for a device

        Args:
            device_id: Device ID
            alerts: List of alert dictionaries

        Returns:
            bool: True if cached successfully
        """
        try:
            key = f"alerts:recent:{device_id}"
            value = json.dumps(alerts, default=str)
            self.client.setex(key, self.TTL_ALERTS, value)
            return True
        except Exception as e:
            logger.error(f"Error caching alerts for {device_id}: {e}")
            return False

    def get_recent_alerts(self, device_id: str) -> Optional[List[Dict]]:
        """
        Get recent alerts from cache

        Args:
            device_id: Device ID

        Returns:
            List of alert dictionaries or None
        """
        try:
            key = f"alerts:recent:{device_id}"
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting alerts from cache: {e}")
            return None

    # ============================================================================
    # STATISTICS CACHING
    # ============================================================================

    def cache_stats(self, stat_key: str, stat_data: Any) -> bool:
        """
        Cache statistical data

        Args:
            stat_key: Statistics key (e.g., "device_count", "alert_summary")
            stat_data: Statistics data (will be JSON serialized)

        Returns:
            bool: True if cached successfully
        """
        try:
            key = f"stats:{stat_key}"
            value = json.dumps(stat_data, default=str)
            self.client.setex(key, self.TTL_STATS, value)
            return True
        except Exception as e:
            logger.error(f"Error caching stats {stat_key}: {e}")
            return False

    def get_stats(self, stat_key: str) -> Optional[Any]:
        """
        Get statistics from cache

        Args:
            stat_key: Statistics key

        Returns:
            Statistics data or None
        """
        try:
            key = f"stats:{stat_key}"
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting stats {stat_key}: {e}")
            return None

    # ============================================================================
    # CACHE MANAGEMENT
    # ============================================================================

    def flush_all(self) -> bool:
        """
        Flush all cached data (use with caution!)

        Returns:
            bool: True if flushed successfully
        """
        try:
            self.client.flushdb()
            logger.warning("All cache data flushed")
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return False

    def get_cache_info(self) -> Dict:
        """
        Get cache statistics and information

        Returns:
            Dictionary with cache info
        """
        try:
            info = self.client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'N/A'),
                'used_memory_peak': info.get('used_memory_peak_human', 'N/A'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {}

    def close(self):
        """Close Redis connection"""
        try:
            self.pool.disconnect()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


# ============================================================================
# CACHE DECORATORS
# ============================================================================

def cached(ttl: int = 60, key_prefix: str = "cached"):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Cache key prefix

    Usage:
        @cached(ttl=300, key_prefix="device_list")
        def get_devices():
            return expensive_db_query()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(arg) for arg in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in kwargs.items())}"

            # Try to get from cache
            cache = get_redis_cache()
            if cache:
                try:
                    cached_value = cache.client.get(cache_key)
                    if cached_value:
                        logger.debug(f"Cache hit: {cache_key}")
                        return json.loads(cached_value)
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            if cache and result is not None:
                try:
                    value_str = json.dumps(result, default=str)
                    cache.client.setex(cache_key, ttl, value_str)
                    logger.debug(f"Cache set: {cache_key}")
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")

            return result

        return wrapper
    return decorator


# Module-level singleton instance
_redis_cache = None


def init_redis_cache(config: Dict) -> RedisCache:
    """
    Initialize the Redis cache singleton

    Args:
        config: Redis configuration dict

    Returns:
        RedisCache: Initialized Redis cache instance
    """
    global _redis_cache
    _redis_cache = RedisCache(config)
    return _redis_cache


def get_redis_cache() -> Optional[RedisCache]:
    """
    Get the Redis cache singleton instance

    Returns:
        RedisCache or None: Redis cache instance if initialized
    """
    return _redis_cache

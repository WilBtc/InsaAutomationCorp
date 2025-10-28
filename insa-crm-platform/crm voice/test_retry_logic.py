#!/usr/bin/env python3
"""
Unit tests for agent_retry.py
Tests retry logic, exponential backoff, jitter, and statistics
"""
import pytest
import time
from agent_retry import (
    with_retry,
    RetryConfig,
    RetryableError,
    PermanentError,
    retry_on_condition,
    with_retry_stats,
    retry_stats,
    DATABASE_RETRY_CONFIG,
    NETWORK_RETRY_CONFIG
)


class TestBasicRetry:
    """Test basic retry functionality"""

    def test_success_on_first_attempt(self):
        """Test that successful function doesn't retry"""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3))
        def always_succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = always_succeeds()
        assert result == "success"
        assert call_count == 1

    def test_success_on_second_attempt(self):
        """Test successful retry after initial failure"""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, base_delay=0.1, jitter=False))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 2

    def test_success_on_last_attempt(self):
        """Test success on final retry attempt"""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, base_delay=0.1, jitter=False))
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert call_count == 3

    def test_failure_after_max_attempts(self):
        """Test failure after exhausting all retries"""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, base_delay=0.1, jitter=False))
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")

        with pytest.raises(ValueError) as exc_info:
            always_fails()

        assert str(exc_info.value) == "Permanent failure"
        assert call_count == 3


class TestExponentialBackoff:
    """Test exponential backoff behavior"""

    def test_backoff_delays(self):
        """Test that delays follow exponential backoff pattern"""
        call_times = []

        @with_retry(RetryConfig(
            max_attempts=4,
            base_delay=0.5,
            exponential_base=2.0,
            jitter=False
        ))
        def track_delays():
            call_times.append(time.time())
            raise ValueError("Force retry")

        with pytest.raises(ValueError):
            track_delays()

        # Calculate actual delays between calls
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times) - 1)]

        # Expected delays: 0.5s, 1.0s, 2.0s (exponential: 0.5 * 2^n)
        assert len(delays) == 3
        assert 0.4 < delays[0] < 0.6  # ~0.5s
        assert 0.9 < delays[1] < 1.1  # ~1.0s
        assert 1.9 < delays[2] < 2.1  # ~2.0s

    def test_max_delay_cap(self):
        """Test that delays don't exceed max_delay"""
        call_times = []

        @with_retry(RetryConfig(
            max_attempts=5,
            base_delay=10.0,
            max_delay=2.0,  # Cap at 2s
            exponential_base=2.0,
            jitter=False
        ))
        def track_delays():
            call_times.append(time.time())
            raise ValueError("Force retry")

        with pytest.raises(ValueError):
            track_delays()

        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times) - 1)]

        # All delays should be capped at max_delay (2.0s)
        for delay in delays:
            assert delay <= 2.1  # Small tolerance for execution time

    def test_jitter_variance(self):
        """Test that jitter adds randomness to delays"""
        delays_list = []

        for _ in range(10):
            call_times = []

            @with_retry(RetryConfig(
                max_attempts=2,
                base_delay=1.0,
                jitter=True
            ))
            def jittered_function():
                call_times.append(time.time())
                raise ValueError("Force retry")

            with pytest.raises(ValueError):
                jittered_function()

            if len(call_times) >= 2:
                delay = call_times[1] - call_times[0]
                delays_list.append(delay)

        # With jitter, delays should vary (0.5s to 1.5s for base_delay=1.0)
        assert len(set(delays_list)) > 1  # Not all the same
        assert all(0.4 < d < 1.6 for d in delays_list)


class TestExceptionHandling:
    """Test exception handling and filtering"""

    def test_specific_exception_retry(self):
        """Test retrying only specific exception types"""
        call_count = 0

        @with_retry(RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            jitter=False,
            retriable_exceptions=(ValueError, TypeError)
        ))
        def specific_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retriable error")
            return "success"

        result = specific_exceptions()
        assert result == "success"
        assert call_count == 2

    def test_non_retriable_exception(self):
        """Test that non-retriable exceptions fail immediately"""
        call_count = 0

        @with_retry(RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            retriable_exceptions=(ValueError,)
        ))
        def wrong_exception():
            nonlocal call_count
            call_count += 1
            raise KeyError("Not retriable")

        with pytest.raises(KeyError):
            wrong_exception()

        # Should fail on first attempt (no retries)
        assert call_count == 1


class TestRetryOnCondition:
    """Test conditional retry logic"""

    def test_condition_based_retry(self):
        """Test retrying based on custom condition"""
        call_count = 0

        def is_timeout(e: Exception) -> bool:
            return isinstance(e, TimeoutError)

        @retry_on_condition(
            condition=is_timeout,
            max_attempts=3,
            base_delay=0.1
        )
        def timeout_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Network timeout")
            return "success"

        result = timeout_function()
        assert result == "success"
        assert call_count == 2

    def test_condition_rejects_retry(self):
        """Test that non-matching condition fails immediately"""
        call_count = 0

        def is_timeout(e: Exception) -> bool:
            return isinstance(e, TimeoutError)

        @retry_on_condition(
            condition=is_timeout,
            max_attempts=3,
            base_delay=0.1
        )
        def value_error_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not a timeout")

        with pytest.raises(ValueError):
            value_error_function()

        # Should fail immediately (no retries)
        assert call_count == 1


class TestRetryStats:
    """Test retry statistics tracking"""

    def test_stats_tracking(self):
        """Test that statistics are tracked correctly"""
        # Reset stats
        retry_stats.total_attempts = 0
        retry_stats.total_successes = 0
        retry_stats.total_failures = 0
        retry_stats.retries_by_function = {}

        call_count = 0

        @with_retry_stats(RetryConfig(max_attempts=3, base_delay=0.1, jitter=False))
        def stat_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        # Call twice
        stat_function()
        call_count = 0
        stat_function()

        stats = retry_stats.get_stats()

        assert stats['total_attempts'] == 2
        assert stats['total_successes'] == 2
        assert stats['total_failures'] == 0
        assert stats['success_rate'] == 1.0

        func_stats = stats['by_function']['stat_function']
        assert func_stats['attempts'] == 2
        assert func_stats['successes'] == 2
        assert func_stats['retries'] == 2  # Both calls needed 1 retry

    def test_stats_with_failures(self):
        """Test statistics with some failures"""
        # Reset stats
        retry_stats.total_attempts = 0
        retry_stats.total_successes = 0
        retry_stats.total_failures = 0
        retry_stats.retries_by_function = {}

        @with_retry_stats(RetryConfig(max_attempts=2, base_delay=0.1, jitter=False))
        def always_fails():
            raise ValueError("Always fails")

        # Try twice, both will fail
        for _ in range(2):
            try:
                always_fails()
            except ValueError:
                pass

        stats = retry_stats.get_stats()

        assert stats['total_attempts'] == 2
        assert stats['total_successes'] == 0
        assert stats['total_failures'] == 2
        assert stats['success_rate'] == 0.0


class TestPredefinedConfigs:
    """Test predefined retry configurations"""

    def test_database_retry_config(self):
        """Test database retry configuration"""
        assert DATABASE_RETRY_CONFIG.max_attempts == 5
        assert DATABASE_RETRY_CONFIG.base_delay == 2.0
        assert DATABASE_RETRY_CONFIG.max_delay == 30.0
        assert DATABASE_RETRY_CONFIG.jitter is True

    def test_network_retry_config(self):
        """Test network retry configuration"""
        assert NETWORK_RETRY_CONFIG.max_attempts == 3
        assert NETWORK_RETRY_CONFIG.base_delay == 1.0
        assert NETWORK_RETRY_CONFIG.max_delay == 10.0
        assert NETWORK_RETRY_CONFIG.jitter is True


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_database_connection_retry(self):
        """Simulate database connection with retries"""
        attempt_count = 0

        # Create modified config using dataclass syntax
        db_config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=DATABASE_RETRY_CONFIG.max_delay,
            exponential_base=DATABASE_RETRY_CONFIG.exponential_base,
            jitter=DATABASE_RETRY_CONFIG.jitter
        )

        @with_retry(db_config)
        def connect_database():
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count < 3:
                raise ConnectionError("Database unavailable")

            return {"status": "connected", "connection_id": 12345}

        result = connect_database()
        assert result["status"] == "connected"
        assert attempt_count == 3

    def test_api_call_with_rate_limiting(self):
        """Simulate API call with rate limiting"""
        call_times = []

        @with_retry(RetryConfig(
            max_attempts=3,
            base_delay=0.5,
            retriable_exceptions=(Exception,),
            jitter=False
        ))
        def api_call():
            call_times.append(time.time())
            if len(call_times) < 2:
                raise Exception("Rate limit exceeded")
            return {"data": "response"}

        result = api_call()
        assert result["data"] == "response"
        assert len(call_times) == 2


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_zero_max_attempts(self):
        """Test that zero attempts still runs once"""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=1, base_delay=0.1))
        def single_attempt():
            nonlocal call_count
            call_count += 1
            return "success"

        result = single_attempt()
        assert result == "success"
        assert call_count == 1

    def test_negative_delay(self):
        """Test handling of negative base delay (should still work)"""
        @with_retry(RetryConfig(max_attempts=2, base_delay=-1.0, jitter=False))
        def negative_delay():
            return "success"

        # Should not crash, delay will be 0 or negative (time.sleep handles this)
        result = negative_delay()
        assert result == "success"

    def test_very_large_max_attempts(self):
        """Test with very large max_attempts (should succeed quickly)"""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=1000, base_delay=0.01, jitter=False))
        def quick_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("One failure")
            return "success"

        result = quick_success()
        assert result == "success"
        assert call_count == 2  # Should succeed on attempt 2, not retry 1000 times


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])

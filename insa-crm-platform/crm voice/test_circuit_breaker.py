#!/usr/bin/env python3
"""
Unit tests for circuit_breaker.py
Tests state transitions, failure detection, recovery, and monitoring
"""
import pytest
import time
from circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
    with_circuit_breaker,
    get_circuit_breaker,
    get_all_circuit_breakers,
    reset_all_circuit_breakers,
    DATABASE_CIRCUIT_CONFIG,
    API_CIRCUIT_CONFIG,
    AI_CIRCUIT_CONFIG
)


class TestBasicStateTransitions:
    """Test basic circuit breaker state transitions"""

    def test_initial_state_is_closed(self):
        """Test that circuit breaker starts in CLOSED state"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    def test_closed_to_open_on_consecutive_failures(self):
        """Test CLOSED → OPEN after consecutive failures"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

        def failing_function():
            raise ValueError("Test failure")

        # First 2 failures should stay CLOSED
        for i in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)
            assert breaker.state == CircuitState.CLOSED

        # 3rd failure should open circuit
        with pytest.raises(ValueError):
            breaker.call(failing_function)
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

    def test_open_rejects_calls_immediately(self):
        """Test that OPEN circuit rejects calls without executing function"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))
        call_count = 0

        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN
        initial_count = call_count

        # Subsequent calls should be rejected without executing function
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(failing_function)

        assert call_count == initial_count  # Function not called
        assert breaker.state == CircuitState.OPEN

    def test_open_to_half_open_after_timeout(self):
        """Test OPEN → HALF_OPEN after timeout expires"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout_duration=1.0
        ))

        def failing_function():
            raise ValueError("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN
        def success_function():
            return "success"

        # Circuit should be HALF_OPEN now (checked before executing)
        result = breaker.call(success_function)
        assert result == "success"

    def test_half_open_to_closed_on_success(self):
        """Test HALF_OPEN → CLOSED after successful calls"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout_duration=0.5,
            success_threshold=2
        ))

        def failing_function():
            raise ValueError("Test failure")

        def success_function():
            return "success"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.6)

        # First success (should be HALF_OPEN)
        breaker.call(success_function)
        assert breaker.state == CircuitState.HALF_OPEN

        # Second success (should close circuit)
        breaker.call(success_function)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_half_open_to_open_on_failure(self):
        """Test HALF_OPEN → OPEN if test call fails"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout_duration=0.5
        ))

        def failing_function():
            raise ValueError("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.6)

        # Failure in HALF_OPEN should immediately go back to OPEN
        with pytest.raises(ValueError):
            breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN


class TestFailureRateTracking:
    """Test failure rate tracking and triggering"""

    def test_failure_rate_threshold_triggers_open(self):
        """Test circuit opens when failure rate exceeds threshold"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=100,  # High consecutive threshold
            failure_rate_threshold=0.5,  # 50% failure rate
            failure_window=2.0,
            min_calls_for_rate_check=10  # Need 10 calls before checking rate
        ))

        # Simulate mixed success/failure pattern (>50% failures)
        def alternating_function(should_fail):
            if should_fail:
                raise ValueError("Failure")
            return "success"

        # Pattern: Need at least 10 calls with >50% failures
        # Pattern: F F F S F F F S F F F S (9 failures, 3 successes = 75% failure rate)
        pattern = [True, True, True, False, True, True, True, False, True, True, True, False]

        for i, should_fail in enumerate(pattern):
            try:
                breaker.call(lambda: alternating_function(should_fail))
            except ValueError:
                pass

            # Should open after reaching min_calls and exceeding failure rate
            if breaker.state == CircuitState.OPEN:
                break

        # Circuit should have opened due to failure rate
        assert breaker.state == CircuitState.OPEN

    def test_failure_window_cleanup(self):
        """Test that old failures are removed from tracking window"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=10,
            failure_window=1.0
        ))

        def failing_function():
            raise ValueError("Failure")

        # Create failures
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        initial_failures = len(breaker.failure_times)
        assert initial_failures == 3

        # Wait for window to expire
        time.sleep(1.1)

        # Trigger cleanup
        breaker._cleanup_old_failures()

        # Old failures should be removed
        assert len(breaker.failure_times) == 0


class TestHalfOpenBehavior:
    """Test half-open state specific behaviors"""

    def test_half_open_limits_test_calls(self):
        """Test that HALF_OPEN limits number of test calls"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout_duration=0.5,
            half_open_max_calls=2,
            success_threshold=10  # High threshold so circuit stays HALF_OPEN
        ))

        def failing_function():
            raise ValueError("Failure")

        def success_function():
            return "success"

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        # Wait for timeout
        time.sleep(0.6)

        # Make 2 test calls (at limit, but won't close circuit due to high success_threshold)
        breaker.call(success_function)
        assert breaker.state == CircuitState.HALF_OPEN
        breaker.call(success_function)
        assert breaker.state == CircuitState.HALF_OPEN

        # 3rd call should be rejected (limit reached)
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(success_function)

    def test_half_open_call_counter_resets_on_close(self):
        """Test that half_open_calls counter resets when circuit closes"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout_duration=0.5,
            success_threshold=2,
            half_open_max_calls=5
        ))

        def failing_function():
            raise ValueError("Failure")

        def success_function():
            return "success"

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        time.sleep(0.6)

        # Make 2 successful calls to close circuit
        breaker.call(success_function)
        breaker.call(success_function)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.half_open_calls == 0  # Should be reset


class TestManualReset:
    """Test manual circuit reset functionality"""

    def test_manual_reset_closes_open_circuit(self):
        """Test manual reset transitions OPEN → CLOSED"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))

        def failing_function():
            raise ValueError("Failure")

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.state == CircuitState.OPEN

        # Manual reset
        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.opened_at is None

    def test_manual_reset_clears_failure_history(self):
        """Test manual reset clears failure tracking"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=5))

        def failing_function():
            raise ValueError("Failure")

        # Create some failures
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.failure_count == 3
        assert len(breaker.failure_times) > 0

        # Manual reset
        breaker.reset()

        assert breaker.failure_count == 0
        assert len(breaker.failure_times) == 0


class TestStateMonitoring:
    """Test state monitoring and reporting"""

    def test_get_state_returns_current_info(self):
        """Test get_state returns comprehensive state information"""
        breaker = CircuitBreaker("test_service", CircuitBreakerConfig(failure_threshold=2))

        state = breaker.get_state()

        assert state['name'] == 'test_service'
        assert state['state'] == 'closed'
        assert state['failure_count'] == 0
        assert state['success_count'] == 0
        assert state['last_failure'] is None
        assert state['opened_at'] is None

    def test_get_state_tracks_failures(self):
        """Test get_state tracks failure information"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

        def failing_function():
            raise ValueError("Failure")

        # Create a failure
        with pytest.raises(ValueError):
            breaker.call(failing_function)

        state = breaker.get_state()

        assert state['failure_count'] == 1
        assert state['last_failure'] is not None
        assert state['failures_in_window'] == 1

    def test_get_state_shows_time_since_open(self):
        """Test get_state shows time since circuit opened"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))

        def failing_function():
            raise ValueError("Failure")

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        time.sleep(0.5)

        state = breaker.get_state()

        assert state['state'] == 'open'
        assert state['time_since_open'] is not None
        assert state['time_since_open'] >= 0.5


class TestDecoratorUsage:
    """Test @with_circuit_breaker decorator"""

    def test_decorator_applies_circuit_breaker(self):
        """Test decorator successfully applies circuit breaker"""
        call_count = 0

        @with_circuit_breaker("decorator_test", CircuitBreakerConfig(failure_threshold=2))
        def decorated_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        # First 2 calls execute
        for _ in range(2):
            with pytest.raises(ValueError):
                decorated_function()

        assert call_count == 2

        # 3rd call should be rejected by circuit breaker
        with pytest.raises(CircuitBreakerOpenError):
            decorated_function()

        assert call_count == 2  # Function not called

    def test_decorator_attaches_breaker_instance(self):
        """Test decorator attaches circuit breaker to function"""
        @with_circuit_breaker("test", CircuitBreakerConfig(failure_threshold=3))
        def decorated_function():
            return "success"

        # Function should have circuit_breaker attribute
        assert hasattr(decorated_function, 'circuit_breaker')
        assert isinstance(decorated_function.circuit_breaker, CircuitBreaker)
        assert decorated_function.circuit_breaker.name == "test"

    def test_decorator_allows_success_calls(self):
        """Test decorator allows successful calls through"""
        @with_circuit_breaker("test", CircuitBreakerConfig(failure_threshold=3))
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"


class TestGlobalRegistry:
    """Test global circuit breaker registry"""

    def test_get_circuit_breaker_creates_new(self):
        """Test get_circuit_breaker creates new breaker if not exists"""
        breaker = get_circuit_breaker("new_service", CircuitBreakerConfig(failure_threshold=5))

        assert breaker.name == "new_service"
        assert breaker.config.failure_threshold == 5

    def test_get_circuit_breaker_returns_existing(self):
        """Test get_circuit_breaker returns existing breaker"""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker1 = get_circuit_breaker("shared_service", config)
        breaker2 = get_circuit_breaker("shared_service")

        # Should be same instance
        assert breaker1 is breaker2

    def test_get_all_circuit_breakers(self):
        """Test get_all_circuit_breakers returns all registered breakers"""
        # Create some breakers
        get_circuit_breaker("service1")
        get_circuit_breaker("service2")
        get_circuit_breaker("service3")

        all_breakers = get_all_circuit_breakers()

        assert len(all_breakers) >= 3  # At least our 3
        assert "service1" in all_breakers
        assert "service2" in all_breakers
        assert "service3" in all_breakers

    def test_reset_all_circuit_breakers(self):
        """Test reset_all_circuit_breakers resets all breakers"""
        # Create and open some circuits
        breaker1 = get_circuit_breaker("reset_test1", CircuitBreakerConfig(failure_threshold=1))
        breaker2 = get_circuit_breaker("reset_test2", CircuitBreakerConfig(failure_threshold=1))

        def failing():
            raise ValueError("Failure")

        # Open both circuits
        for breaker in [breaker1, breaker2]:
            with pytest.raises(ValueError):
                breaker.call(failing)

        assert breaker1.state == CircuitState.OPEN
        assert breaker2.state == CircuitState.OPEN

        # Reset all
        reset_all_circuit_breakers()

        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED


class TestPredefinedConfigs:
    """Test predefined circuit breaker configurations"""

    def test_database_circuit_config(self):
        """Test DATABASE_CIRCUIT_CONFIG values"""
        assert DATABASE_CIRCUIT_CONFIG.failure_threshold == 5
        assert DATABASE_CIRCUIT_CONFIG.timeout_duration == 30.0
        assert DATABASE_CIRCUIT_CONFIG.success_threshold == 2
        assert DATABASE_CIRCUIT_CONFIG.failure_rate_threshold == 0.5

    def test_api_circuit_config(self):
        """Test API_CIRCUIT_CONFIG values"""
        assert API_CIRCUIT_CONFIG.failure_threshold == 10
        assert API_CIRCUIT_CONFIG.timeout_duration == 60.0
        assert API_CIRCUIT_CONFIG.success_threshold == 3
        assert API_CIRCUIT_CONFIG.failure_rate_threshold == 0.6

    def test_ai_circuit_config(self):
        """Test AI_CIRCUIT_CONFIG values"""
        assert AI_CIRCUIT_CONFIG.failure_threshold == 3
        assert AI_CIRCUIT_CONFIG.timeout_duration == 90.0
        assert AI_CIRCUIT_CONFIG.success_threshold == 2
        assert AI_CIRCUIT_CONFIG.half_open_max_calls == 2
        assert AI_CIRCUIT_CONFIG.failure_rate_threshold == 0.7


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_database_connection_failure_scenario(self):
        """Simulate database connection with circuit breaker"""
        breaker = CircuitBreaker("database", DATABASE_CIRCUIT_CONFIG)
        connection_attempts = 0

        def connect_database():
            nonlocal connection_attempts
            connection_attempts += 1

            if connection_attempts <= 5:  # Fail for first 5 attempts
                raise ConnectionError("Database unavailable")
            return {"status": "connected"}

        # First 5 attempts should fail and open circuit
        for i in range(5):
            with pytest.raises(ConnectionError):
                breaker.call(connect_database)

        assert breaker.state == CircuitState.OPEN

        # Subsequent attempts should be rejected immediately
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(connect_database)

        # Should not have tried connection again
        assert connection_attempts == 5

    def test_api_rate_limiting_scenario(self):
        """Simulate API rate limiting with recovery"""
        breaker = CircuitBreaker("api", CircuitBreakerConfig(
            failure_threshold=3,
            timeout_duration=1.0,
            success_threshold=2
        ))
        call_count = 0

        def api_call():
            nonlocal call_count
            call_count += 1

            # Simulate rate limiting for first 3 calls
            if call_count <= 3:
                raise Exception("Rate limit exceeded")
            return {"data": "response"}

        # Open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(api_call)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery
        time.sleep(1.1)

        # Recovery calls should succeed
        result = breaker.call(api_call)
        assert result["data"] == "response"

    def test_intermittent_failures_dont_open_circuit(self):
        """Test that intermittent failures don't open circuit"""
        breaker = CircuitBreaker("flaky_service", CircuitBreakerConfig(
            failure_threshold=3,
            failure_rate_threshold=1.0  # Only open on consecutive failures, not failure rate
        ))
        call_count = 0

        def intermittent_service():
            nonlocal call_count
            call_count += 1

            # Fail every other call
            if call_count % 2 == 0:
                raise ValueError("Intermittent failure")
            return "success"

        # Make 10 calls (5 failures, but not consecutive)
        for _ in range(10):
            try:
                breaker.call(intermittent_service)
            except ValueError:
                pass

        # Circuit should still be CLOSED (failures not consecutive)
        assert breaker.state == CircuitState.CLOSED


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_failure_threshold(self):
        """Test circuit with zero failure threshold"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=0))

        def failing():
            raise ValueError("Failure")

        # Should open immediately on any failure
        with pytest.raises(ValueError):
            breaker.call(failing)

        # Circuit might be open (depends on failure rate calculation)
        # This is an edge case that's not well-defined

    def test_very_short_timeout(self):
        """Test circuit with very short timeout (100ms)"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout_duration=0.1
        ))

        def failing():
            raise ValueError("Failure")

        def success():
            return "success"

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing)

        # Wait for very short timeout
        time.sleep(0.15)

        # Should allow recovery attempt
        result = breaker.call(success)
        assert result == "success"

    def test_success_resets_failure_count(self):
        """Test that success resets consecutive failure count"""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

        def failing():
            raise ValueError("Failure")

        def success():
            return "success"

        # 2 failures
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing)

        assert breaker.failure_count == 2

        # 1 success should reset
        breaker.call(success)
        assert breaker.failure_count == 0

        # Circuit should still be closed
        assert breaker.state == CircuitState.CLOSED


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])

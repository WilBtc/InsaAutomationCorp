#!/usr/bin/env python3
"""
Circuit Breaker for INSA CRM Multi-Agent System
Prevents cascading failures by "opening" the circuit when error rate exceeds threshold

State Machine:
CLOSED (normal operation)
   ↓ (failure threshold exceeded)
OPEN (reject requests immediately)
   ↓ (timeout expires)
HALF_OPEN (test if service recovered)
   ↓ (success) → CLOSED
   ↓ (failure) → OPEN
"""
import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict
from functools import wraps
from dataclasses import dataclass
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5          # Open after N consecutive failures
    timeout_duration: float = 60.0      # Seconds to wait before HALF_OPEN
    success_threshold: int = 2          # Successes needed to close from HALF_OPEN
    half_open_max_calls: int = 3        # Max calls allowed in HALF_OPEN state
    failure_window: float = 60.0        # Window for tracking failure rate
    failure_rate_threshold: float = 0.5  # Open if >50% failures in window
    min_calls_for_rate_check: int = 10  # Min calls before checking failure rate


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures

    Features:
    - State transitions: CLOSED → OPEN → HALF_OPEN → CLOSED
    - Automatic recovery testing
    - Failure rate tracking (time-based window)
    - Comprehensive logging
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker

        Args:
            name: Circuit breaker name (for logging)
            config: Configuration (defaults to CircuitBreakerConfig())
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None
        self.opened_at = None

        # Time-based failure tracking
        self.failure_times = deque()  # Track timestamps of failures
        self.total_calls = 0  # Track total calls for failure rate

        logger.info(f"Circuit breaker '{self.name}' initialized (state: CLOSED)")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
        """
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"🔄 Circuit breaker '{self.name}': OPEN → HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.half_open_calls = 0
            else:
                time_since_open = time.time() - self.opened_at if self.opened_at else 0
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN "
                    f"(opened {time_since_open:.0f}s ago, retry in {self.config.timeout_duration - time_since_open:.0f}s)"
                )

        # HALF_OPEN: limit number of test calls
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                logger.warning(f"⚠️ Circuit breaker '{self.name}': HALF_OPEN call limit reached, waiting...")
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is HALF_OPEN (test calls exhausted)"
                )
            self.half_open_calls += 1

        # Track call (only in CLOSED state for statistics)
        if self.state == CircuitState.CLOSED:
            self.total_calls += 1

        # Attempt to execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """
        Check if enough time has passed to test recovery

        Returns:
            True if should attempt reset to HALF_OPEN
        """
        if self.opened_at is None:
            return False
        return time.time() - self.opened_at >= self.config.timeout_duration

    def _on_success(self):
        """Handle successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.config.success_threshold:
                logger.info(f"✅ Circuit breaker '{self.name}': HALF_OPEN → CLOSED (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.half_open_calls = 0
                self.opened_at = None
                self.failure_times.clear()
                self.total_calls = 0

        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self, exception: Exception):
        """
        Handle failed execution

        Args:
            exception: Exception that was raised
        """
        current_time = time.time()
        self.failure_count += 1
        self.last_failure_time = current_time

        # Track failure in time window
        self.failure_times.append(current_time)
        self._cleanup_old_failures()

        if self.state == CircuitState.HALF_OPEN:
            # Immediate fail-back to OPEN
            logger.warning(
                f"⚠️ Circuit breaker '{self.name}': HALF_OPEN → OPEN "
                f"(recovery test failed: {type(exception).__name__})"
            )
            self.state = CircuitState.OPEN
            self.opened_at = time.time()
            self.success_count = 0
            self.half_open_calls = 0

        elif self.state == CircuitState.CLOSED:
            # Check if should open (consecutive failures OR failure rate)
            should_open = False

            # Check consecutive failures
            if self.failure_count >= self.config.failure_threshold:
                logger.error(
                    f"❌ Circuit breaker '{self.name}': CLOSED → OPEN "
                    f"({self.failure_count} consecutive failures)"
                )
                should_open = True

            # Check failure rate (only after minimum calls)
            if self.total_calls >= self.config.min_calls_for_rate_check:
                failure_rate = self._calculate_failure_rate()
                if failure_rate >= self.config.failure_rate_threshold:
                    logger.error(
                        f"❌ Circuit breaker '{self.name}': CLOSED → OPEN "
                        f"(failure rate {failure_rate:.1%} > threshold {self.config.failure_rate_threshold:.1%})"
                    )
                    should_open = True

            if should_open:
                self.state = CircuitState.OPEN
                self.opened_at = time.time()

    def _cleanup_old_failures(self):
        """Remove failures older than failure_window"""
        cutoff_time = time.time() - self.config.failure_window

        while self.failure_times and self.failure_times[0] < cutoff_time:
            self.failure_times.popleft()

    def _calculate_failure_rate(self) -> float:
        """
        Calculate failure rate in the current window

        Returns:
            Failure rate (0.0 to 1.0)
        """
        if self.total_calls == 0:
            return 0.0

        failures = len(self.failure_times)
        return failures / self.total_calls

    def get_state(self) -> Dict[str, Any]:
        """
        Get current circuit breaker state

        Returns:
            State dictionary
        """
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure': datetime.fromtimestamp(self.last_failure_time).isoformat() if self.last_failure_time else None,
            'opened_at': datetime.fromtimestamp(self.opened_at).isoformat() if self.opened_at else None,
            'time_since_open': time.time() - self.opened_at if self.opened_at else None,
            'failure_rate': self._calculate_failure_rate(),
            'failures_in_window': len(self.failure_times)
        }

    def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        logger.info(f"🔄 Circuit breaker '{self.name}': Manual reset to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.opened_at = None
        self.last_failure_time = None
        self.failure_times.clear()
        self.total_calls = 0


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


def with_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator for adding circuit breaker protection.

    Usage:
        @with_circuit_breaker("claude_api", CircuitBreakerConfig(failure_threshold=3))
        def call_claude_api():
            # Your code here
            pass

    Args:
        name: Circuit breaker name
        config: Configuration (optional)

    Returns:
        Decorated function
    """
    breaker = CircuitBreaker(name, config)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)

        # Attach breaker to function for testing/monitoring
        wrapper.circuit_breaker = breaker
        return wrapper
    return decorator


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """
    Get or create a circuit breaker

    Args:
        name: Circuit breaker name
        config: Configuration (only used if creating new)

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """
    Get all registered circuit breakers

    Returns:
        Dictionary of circuit breakers
    """
    return _circuit_breakers.copy()


def reset_all_circuit_breakers():
    """Reset all circuit breakers to CLOSED state"""
    for breaker in _circuit_breakers.values():
        breaker.reset()


# Predefined circuit breaker configurations

# Database operations (strict: 5 failures, 30s timeout)
DATABASE_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    timeout_duration=30.0,
    success_threshold=2,
    failure_window=60.0,
    failure_rate_threshold=0.5,
    min_calls_for_rate_check=10
)

# External APIs (lenient: 10 failures, 60s timeout)
API_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=10,
    timeout_duration=60.0,
    success_threshold=3,
    failure_window=120.0,
    failure_rate_threshold=0.6,
    min_calls_for_rate_check=20
)

# AI Services (very lenient: 3 failures, 90s timeout)
AI_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,
    timeout_duration=90.0,
    success_threshold=2,
    half_open_max_calls=2,
    failure_window=180.0,
    failure_rate_threshold=0.7,
    min_calls_for_rate_check=5
)


if __name__ == '__main__':
    # Demo: Test circuit breaker state transitions
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("CIRCUIT BREAKER DEMO")
    print("=" * 60)

    # Example 1: CLOSED → OPEN after failures
    print("\n1. Testing CLOSED → OPEN transition...")
    call_count = 0

    @with_circuit_breaker("demo_api", CircuitBreakerConfig(failure_threshold=3, timeout_duration=2.0))
    def flaky_api():
        global call_count
        call_count += 1
        print(f"   Call {call_count}")
        raise ValueError("API failure")

    # Cause failures to open circuit
    for i in range(5):
        try:
            flaky_api()
        except (ValueError, CircuitBreakerOpenError) as e:
            print(f"   Attempt {i+1}: {type(e).__name__}")

    # Check state
    state = flaky_api.circuit_breaker.get_state()
    print(f"   State: {state['state']} (failures: {state['failure_count']})")

    # Example 2: OPEN → HALF_OPEN → CLOSED recovery
    print("\n2. Testing recovery (OPEN → HALF_OPEN → CLOSED)...")
    print("   Waiting 2s for timeout...")
    time.sleep(2.1)

    # Use global for demo simplicity
    global recovery_count
    recovery_count = 0

    @with_circuit_breaker("recovery_api", CircuitBreakerConfig(
        failure_threshold=2,
        timeout_duration=1.0,
        success_threshold=2
    ))
    def recovering_api():
        global recovery_count
        recovery_count += 1
        if recovery_count <= 2:
            raise ValueError("Still failing")
        return "success"

    # Cause failures to open
    for i in range(3):
        try:
            recovering_api()
        except ValueError:
            print(f"   Failure {i+1}")

    print(f"   State after failures: {recovering_api.circuit_breaker.state.value}")

    # Wait for timeout
    time.sleep(1.1)

    # Recovery attempts
    for i in range(4):
        try:
            result = recovering_api()
            print(f"   Recovery attempt {i+1}: {result}")
        except (ValueError, CircuitBreakerOpenError) as e:
            print(f"   Recovery attempt {i+1}: {type(e).__name__}")

    print(f"   Final state: {recovering_api.circuit_breaker.state.value}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)

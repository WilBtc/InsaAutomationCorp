"""
Circuit Breaker Pattern Implementation
Phase 12: Production Hardening - Week 1, Day 1-2

Prevents cascading failures by detecting failing services and temporarily
stopping calls to them, giving them time to recover.

Circuit States:
- CLOSED: Normal operation, all requests pass through
- OPEN: Too many failures, reject all requests immediately
- HALF_OPEN: Allow limited requests to test if service recovered

Features:
- Automatic state transitions based on failure thresholds
- Configurable failure threshold and timeout
- Thread-safe operation
- Detailed logging of state changes
- Compatible with any function via decorator pattern

Usage:
    from circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=5, timeout=60)

    @breaker
    def call_external_service():
        return requests.get("http://external-api.com/data")

    # If service fails 5 times, circuit opens for 60 seconds

Author: Claude Code + Wil Aroca
Created: October 31, 2025
"""

import time
import threading
import logging
from enum import Enum
from typing import Callable, Any, Optional, Type
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """
    Circuit breaker states

    CLOSED: Normal operation - all requests pass through
    OPEN: Service failing - reject requests immediately (fail fast)
    HALF_OPEN: Testing recovery - allow limited requests through
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __str__(self):
        return self.value.upper()


class CircuitBreakerOpenError(Exception):
    """
    Exception raised when circuit breaker is OPEN

    This is raised instead of calling the wrapped function to fail fast
    when the service is known to be unavailable.
    """
    def __init__(self, function_name: str, timeout_remaining: float):
        self.function_name = function_name
        self.timeout_remaining = timeout_remaining
        super().__init__(
            f"Circuit breaker OPEN for {function_name}. "
            f"Service unavailable. Retry in {timeout_remaining:.1f}s"
        )


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures

    The circuit breaker monitors function calls and tracks failures.
    When failures exceed the threshold, the circuit opens and rejects
    all calls for a timeout period. After timeout, it enters HALF_OPEN
    state to test if the service recovered.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Too many failures, reject all requests immediately
    - HALF_OPEN: Allow limited requests to test if service recovered

    Parameters:
        failure_threshold: Number of failures before opening circuit (default: 5)
        timeout: Seconds to wait before testing recovery (default: 60)
        expected_exception: Exception type to catch (default: Exception)
        name: Optional name for logging (default: function name)

    Example:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60)

        @breaker
        def call_claude_code(prompt):
            # If Claude Code fails 5 times, stop calling it for 60 seconds
            return subprocess.run(["claude", "--print", prompt], ...)

        # Use normally - circuit breaker handles failures automatically
        try:
            result = call_claude_code("Size a separator")
        except CircuitBreakerOpenError:
            # Circuit is open - service unavailable
            # Use fallback logic or return error to user
            pass

    Thread Safety:
        This class is thread-safe. Multiple threads can safely call
        functions protected by the same circuit breaker instance.
    """

    def __init__(self,
                 failure_threshold: int = 5,
                 timeout: int = 60,
                 expected_exception: Type[Exception] = Exception,
                 name: Optional[str] = None):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait in OPEN state before testing recovery
            expected_exception: Exception type to catch (subclasses also caught)
            name: Optional name for logging (defaults to function name)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.name = name

        # State tracking
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()

        logger.info(
            f"Circuit breaker initialized: "
            f"threshold={failure_threshold}, timeout={timeout}s"
        )

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to wrap function with circuit breaker

        Args:
            func: Function to protect with circuit breaker

        Returns:
            Wrapped function with circuit breaker logic
        """
        # Use provided name or function name
        breaker_name = self.name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Check circuit state
            with self.lock:
                if self.state == CircuitState.OPEN:
                    # Check if timeout expired
                    time_since_failure = time.time() - self.last_failure_time
                    if time_since_failure >= self.timeout:
                        # Timeout expired - enter HALF_OPEN to test recovery
                        self.state = CircuitState.HALF_OPEN
                        logger.info(
                            f"Circuit breaker {breaker_name}: "
                            f"OPEN → HALF_OPEN (testing recovery)"
                        )
                    else:
                        # Still in timeout - reject request
                        timeout_remaining = self.timeout - time_since_failure
                        logger.warning(
                            f"Circuit breaker {breaker_name}: "
                            f"OPEN - rejecting request "
                            f"(retry in {timeout_remaining:.1f}s)"
                        )
                        raise CircuitBreakerOpenError(breaker_name, timeout_remaining)

            # Attempt to call function
            try:
                result = func(*args, **kwargs)

                # Success - handle state transition
                with self.lock:
                    if self.state == CircuitState.HALF_OPEN:
                        # Service recovered - close circuit
                        self.state = CircuitState.CLOSED
                        self.failure_count = 0
                        logger.info(
                            f"Circuit breaker {breaker_name}: "
                            f"HALF_OPEN → CLOSED (service recovered)"
                        )
                    elif self.state == CircuitState.CLOSED:
                        # Reset failure count on success
                        if self.failure_count > 0:
                            logger.debug(
                                f"Circuit breaker {breaker_name}: "
                                f"Success - resetting failure count from {self.failure_count} to 0"
                            )
                            self.failure_count = 0

                return result

            except self.expected_exception as e:
                # Failure - increment count and maybe open circuit
                with self.lock:
                    self.failure_count += 1
                    self.last_failure_time = time.time()

                    if self.failure_count >= self.failure_threshold:
                        # Threshold reached - open circuit
                        if self.state != CircuitState.OPEN:
                            self.state = CircuitState.OPEN
                            logger.error(
                                f"Circuit breaker {breaker_name}: "
                                f"{self.state} → OPEN "
                                f"(failures: {self.failure_count}/{self.failure_threshold})"
                            )
                    else:
                        # Still below threshold
                        logger.warning(
                            f"Circuit breaker {breaker_name}: "
                            f"Failure {self.failure_count}/{self.failure_threshold} "
                            f"(state: {self.state})"
                        )

                # Re-raise original exception
                raise

        return wrapper

    def reset(self):
        """
        Manually reset circuit breaker to CLOSED state

        This can be used for testing or manual recovery after fixing
        underlying issues.
        """
        with self.lock:
            old_state = self.state
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            logger.info(
                f"Circuit breaker manually reset: {old_state} → CLOSED"
            )

    def get_status(self) -> dict:
        """
        Get current circuit breaker status

        Returns:
            dict: Status information including:
                - state: Current state (CLOSED/OPEN/HALF_OPEN)
                - failure_count: Current failure count
                - failure_threshold: Threshold for opening circuit
                - time_in_state: Seconds in current state
                - timeout_remaining: Seconds until HALF_OPEN (if OPEN)
        """
        with self.lock:
            status = {
                "state": str(self.state),
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "timeout": self.timeout,
            }

            if self.last_failure_time:
                time_since_failure = time.time() - self.last_failure_time
                status["time_since_last_failure"] = time_since_failure

                if self.state == CircuitState.OPEN:
                    status["timeout_remaining"] = max(
                        0,
                        self.timeout - time_since_failure
                    )

            return status


# Convenience circuit breakers for common use cases

# Fast circuit breaker for quick operations (3 failures, 30s timeout)
fast_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=30,
    name="fast_breaker"
)

# Standard circuit breaker for most operations (5 failures, 60s timeout)
standard_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    name="standard_breaker"
)

# Tolerant circuit breaker for flaky services (10 failures, 120s timeout)
tolerant_breaker = CircuitBreaker(
    failure_threshold=10,
    timeout=120,
    name="tolerant_breaker"
)


# Example usage for INSA CRM agent workers
if __name__ == "__main__":
    """
    Example usage and testing
    """
    import subprocess

    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*70)
    print("Circuit Breaker Pattern - Examples")
    print("="*70)

    # Example 1: Protect Claude Code subprocess calls
    print("\n=== Example 1: Protect Claude Code Calls ===")

    claude_breaker = CircuitBreaker(failure_threshold=3, timeout=10, name="claude_code")

    attempt_count = 0

    @claude_breaker
    def call_claude_code_unstable(prompt: str):
        """Simulates Claude Code - fails first 5 times"""
        global attempt_count
        attempt_count += 1

        if attempt_count <= 5:
            raise RuntimeError(f"Claude Code timeout (attempt {attempt_count})")

        return {"response": f"Processed: {prompt}"}

    # Try calling multiple times
    for i in range(8):
        try:
            result = call_claude_code_unstable(f"Request {i+1}")
            print(f"✅ Request {i+1}: SUCCESS - {result}")
        except CircuitBreakerOpenError as e:
            print(f"⚠️  Request {i+1}: CIRCUIT OPEN - {e}")
        except RuntimeError as e:
            print(f"❌ Request {i+1}: FAILED - {e}")

        # Check status
        status = claude_breaker.get_status()
        print(f"   Status: {status['state']} (failures: {status['failure_count']}/{status['failure_threshold']})")

        time.sleep(0.5)

    # Example 2: External API with circuit breaker
    print("\n=== Example 2: External API Protection ===")

    api_breaker = CircuitBreaker(failure_threshold=3, timeout=5, name="external_api")

    @api_breaker
    def call_external_api(endpoint: str):
        """Simulates external API call"""
        # Simulate API call
        import random
        if random.random() < 0.7:  # 70% failure rate
            raise ConnectionError("API connection failed")
        return {"data": "success"}

    successes = 0
    failures = 0
    circuit_opens = 0

    for i in range(20):
        try:
            result = call_external_api(f"/api/endpoint{i}")
            successes += 1
        except CircuitBreakerOpenError:
            circuit_opens += 1
        except ConnectionError:
            failures += 1

        time.sleep(0.1)

    print(f"\nResults:")
    print(f"  Successes: {successes}")
    print(f"  Failures: {failures}")
    print(f"  Circuit Opens: {circuit_opens}")
    print(f"  Total Requests: {successes + failures + circuit_opens}")

    # Example 3: Manual reset
    print("\n=== Example 3: Manual Reset ===")
    print(f"Circuit state before reset: {api_breaker.get_status()['state']}")
    api_breaker.reset()
    print(f"Circuit state after reset: {api_breaker.get_status()['state']}")

    print("\n" + "="*70)
    print("Examples complete")
    print("="*70)

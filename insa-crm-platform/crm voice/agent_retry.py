#!/usr/bin/env python3
"""
Retry Logic for INSA CRM Multi-Agent System
Handles transient failures with exponential backoff and jitter
"""
import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retriable_exceptions: Tuple[Type[Exception], ...] = (Exception,)


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator for adding retry logic to functions with exponential backoff.

    Features:
    - Exponential backoff: delay = base_delay * (exponential_base ^ attempt)
    - Jitter: Random variance to prevent thundering herd
    - Configurable exceptions: Only retry specific exception types
    - Comprehensive logging: Track all retry attempts

    Usage:
        @with_retry(RetryConfig(max_attempts=5, base_delay=2.0))
        def send_message(msg):
            # Your code here
            pass

    Args:
        config: RetryConfig instance (defaults to RetryConfig())

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = func(*args, **kwargs)

                    # Success! Log if this was a retry
                    if attempt > 1:
                        logger.info(
                            f"✅ {func.__name__} succeeded on attempt {attempt}/{config.max_attempts}"
                        )

                    return result

                except config.retriable_exceptions as e:
                    last_exception = e

                    # Last attempt failed - give up
                    if attempt == config.max_attempts:
                        logger.error(
                            f"❌ {func.__name__} failed after {config.max_attempts} attempts: "
                            f"{type(e).__name__}: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )

                    # Add jitter to prevent thundering herd problem
                    # Jitter: random variance of ±50%
                    if config.jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt}/{config.max_attempts} failed: "
                        f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)

            # Should never reach here (last attempt raises)
            raise last_exception

        return wrapper
    return decorator


class RetryableError(Exception):
    """Base exception for retriable errors"""
    pass


class PermanentError(Exception):
    """Exception for non-retriable errors"""
    pass


def retry_on_condition(
    condition: Callable[[Exception], bool],
    max_attempts: int = 3,
    base_delay: float = 1.0
):
    """
    Retry based on a custom condition function.

    Usage:
        @retry_on_condition(
            condition=lambda e: isinstance(e, TimeoutError),
            max_attempts=5
        )
        def flaky_function():
            # Your code here
            pass

    Args:
        condition: Function that returns True if exception is retriable
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if this exception is retriable
                    if not condition(e):
                        logger.error(f"❌ {func.__name__} failed with non-retriable error: {e}")
                        raise

                    if attempt == max_attempts:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)

            raise last_exception

        return wrapper
    return decorator


class RetryStats:
    """Track retry statistics"""

    def __init__(self):
        self.total_attempts = 0
        self.total_successes = 0
        self.total_failures = 0
        self.retries_by_function = {}

    def record_attempt(self, func_name: str, attempt: int, success: bool):
        """Record a retry attempt"""
        self.total_attempts += 1

        if success:
            self.total_successes += 1
        else:
            self.total_failures += 1

        if func_name not in self.retries_by_function:
            self.retries_by_function[func_name] = {
                'attempts': 0,
                'successes': 0,
                'failures': 0,
                'retries': 0
            }

        stats = self.retries_by_function[func_name]
        stats['attempts'] += 1

        if success:
            stats['successes'] += 1
        else:
            stats['failures'] += 1

        if attempt > 1:
            stats['retries'] += 1

    def get_stats(self):
        """Get retry statistics"""
        return {
            'total_attempts': self.total_attempts,
            'total_successes': self.total_successes,
            'total_failures': self.total_failures,
            'success_rate': (
                self.total_successes / self.total_attempts
                if self.total_attempts > 0 else 0
            ),
            'by_function': self.retries_by_function
        }


# Global retry statistics
retry_stats = RetryStats()


def with_retry_stats(config: Optional[RetryConfig] = None):
    """
    Decorator that tracks retry statistics.

    Usage:
        @with_retry_stats(RetryConfig(max_attempts=3))
        def my_function():
            # Your code here
            pass
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            success = False

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    success = True

                    if attempt > 1:
                        logger.info(
                            f"✅ {func.__name__} succeeded on attempt {attempt}/{config.max_attempts}"
                        )

                    # Record success
                    retry_stats.record_attempt(func.__name__, attempt, success=True)
                    return result

                except config.retriable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts:
                        logger.error(
                            f"❌ {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        # Record failure
                        retry_stats.record_attempt(func.__name__, attempt, success=False)
                        raise

                    delay = min(
                        config.base_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )

                    if config.jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt}/{config.max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)

            raise last_exception

        return wrapper
    return decorator


# Predefined retry configurations for common scenarios

# Database operations (5 attempts, 2s base delay)
DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)

# Network operations (3 attempts, 1s base delay)
NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True
)

# API calls (5 attempts, 2s base delay, longer max)
API_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=2.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)

# Fast operations (2 attempts, 0.5s base delay)
FAST_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=0.5,
    max_delay=5.0,
    exponential_base=2.0,
    jitter=True
)


if __name__ == '__main__':
    # Demo: Test retry logic with simulated failures
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("RETRY LOGIC DEMO")
    print("=" * 60)

    # Example 1: Success on second attempt
    print("\n1. Testing success on second attempt...")
    call_count = 0

    @with_retry(RetryConfig(max_attempts=3, base_delay=0.5, jitter=False))
    def flaky_function():
        global call_count
        call_count += 1
        print(f"   Attempt {call_count}")
        if call_count < 2:
            raise ValueError("Temporary failure")
        return "success"

    try:
        result = flaky_function()
        print(f"   ✅ Result: {result}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Example 2: Permanent failure
    print("\n2. Testing permanent failure (all retries exhausted)...")
    call_count2 = 0

    @with_retry(RetryConfig(max_attempts=3, base_delay=0.5, jitter=False))
    def always_fails():
        global call_count2
        call_count2 += 1
        print(f"   Attempt {call_count2}")
        raise ValueError("Permanent failure")

    try:
        result = always_fails()
    except Exception as e:
        print(f"   ❌ Failed after all retries: {e}")

    # Example 3: Retry stats
    print("\n3. Testing retry statistics...")

    @with_retry_stats(RetryConfig(max_attempts=3, base_delay=0.5, jitter=False))
    def stat_test():
        import random
        if random.random() < 0.7:
            raise ValueError("Random failure")
        return "success"

    # Try multiple times
    for i in range(10):
        try:
            stat_test()
        except:
            pass

    stats = retry_stats.get_stats()
    print(f"   Stats: {stats}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)

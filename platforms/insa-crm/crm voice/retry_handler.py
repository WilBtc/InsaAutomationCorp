"""
Retry Handler with Exponential Backoff
Phase 12: Production Hardening - Week 1, Day 1

Provides automatic retry logic with exponential backoff and jitter
for resilient operation of INSA CRM agent workers.

Features:
- Configurable retry attempts (default: 3)
- Exponential backoff with jitter to prevent thundering herd
- Detailed logging of retry attempts
- Compatible with any function via decorator pattern

Usage:
    from retry_handler import with_retry, RetryConfig

    @with_retry(RetryConfig(max_attempts=5))
    def unstable_operation():
        result = call_external_api()
        return result

Author: Claude Code + Wil Aroca
Created: October 31, 2025
"""

import time
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class RetryConfig:
    """
    Configuration for retry behavior

    Parameters:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay in seconds (caps exponential growth) (default: 60.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        jitter: Whether to add random jitter to prevent thundering herd (default: True)

    Example:
        # Retry up to 5 times with faster backoff
        config = RetryConfig(max_attempts=5, initial_delay=0.5, max_delay=30.0)
    """

    def __init__(self,
                 max_attempts: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def __repr__(self):
        return (f"RetryConfig(max_attempts={self.max_attempts}, "
                f"initial_delay={self.initial_delay}, "
                f"max_delay={self.max_delay}, "
                f"exponential_base={self.exponential_base}, "
                f"jitter={self.jitter})")


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator for automatic retry with exponential backoff

    This decorator wraps any function and automatically retries it on failure
    using exponential backoff with optional jitter.

    Parameters:
        config: RetryConfig instance (if None, uses defaults)

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(RetryConfig(max_attempts=5))
        def unstable_operation():
            # This will retry up to 5 times with exponential backoff
            result = call_external_api()
            return result

        # Call it normally - retries happen automatically
        result = unstable_operation()

    Retry Schedule (default config):
    - Attempt 1: Immediate
    - Attempt 2: ~1s delay (0.5-1.5s with jitter)
    - Attempt 3: ~2s delay (1-3s with jitter)
    - Attempt 4+: Capped at max_delay
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    # Attempt the operation
                    result = func(*args, **kwargs)

                    # Log success on retry
                    if attempt > 1:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt}/{config.max_attempts}"
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # If this was the last attempt, raise the exception
                    if attempt == config.max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {attempt} attempts: {e}",
                            exc_info=True
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.initial_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )

                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        import random
                        # Jitter: 50-150% of calculated delay
                        delay = delay * (0.5 + random.random())

                    # Log retry attempt
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{config.max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    # Wait before retry
                    time.sleep(delay)

            # This should never be reached due to raise in loop, but just in case
            raise last_exception

        return wrapper
    return decorator


# Convenience configurations for common use cases

# Quick retry for fast operations (3 attempts, 0.5s initial delay)
QUICK_RETRY = RetryConfig(max_attempts=3, initial_delay=0.5, max_delay=5.0)

# Standard retry for most operations (3 attempts, 1s initial delay)
STANDARD_RETRY = RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=30.0)

# Persistent retry for critical operations (5 attempts, 2s initial delay)
PERSISTENT_RETRY = RetryConfig(max_attempts=5, initial_delay=2.0, max_delay=60.0)

# Aggressive retry for external services (10 attempts, 5s initial delay)
AGGRESSIVE_RETRY = RetryConfig(max_attempts=10, initial_delay=5.0, max_delay=300.0)


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

    # Example 1: Retry unstable network call
    attempt_count = 0

    @with_retry(STANDARD_RETRY)
    def unstable_network_call():
        """Simulates unstable network - fails first 2 times"""
        global attempt_count
        attempt_count += 1

        if attempt_count < 3:
            raise ConnectionError(f"Network timeout (attempt {attempt_count})")

        return {"status": "success", "data": "Hello World"}

    # Test it
    print("\n=== Example 1: Unstable Network Call ===")
    result = unstable_network_call()
    print(f"Result: {result}")

    # Example 2: Retry agent worker operation
    @with_retry(PERSISTENT_RETRY)
    def process_agent_message(message: dict):
        """Process message with Claude Code - may fail due to subprocess issues"""
        # Simulate agent processing
        if not message.get('text'):
            raise ValueError("Message text is required")

        # In real implementation, this would call Claude Code subprocess
        return {
            "success": True,
            "response": f"Processed: {message['text']}"
        }

    print("\n=== Example 2: Agent Message Processing ===")
    message = {"text": "Size a separator for 50 bbl/day"}
    result = process_agent_message(message)
    print(f"Result: {result}")

    # Example 3: Custom configuration
    custom_config = RetryConfig(
        max_attempts=7,
        initial_delay=0.25,
        max_delay=10.0,
        exponential_base=1.5,
        jitter=True
    )

    @with_retry(custom_config)
    def custom_retry_function():
        """Custom retry behavior"""
        return "Success with custom config"

    print("\n=== Example 3: Custom Configuration ===")
    print(f"Config: {custom_config}")
    result = custom_retry_function()
    print(f"Result: {result}")

    print("\n=== All Examples Complete ===")

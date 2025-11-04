#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation (Phase 12 hardened version)

Provides resiliency utilities used across the CRM Voice stack and validated
by the dedicated pytest suite. Features include:

- Configurable thresholds via `CircuitBreakerConfig`
- Consecutive failure tracking and failure-rate monitoring windows
- Automatic CLOSED → OPEN → HALF_OPEN transitions with success gating
- Half-open call limiting to prevent sudden traffic spikes
- Global registry helpers plus decorator support (`with_circuit_breaker`)

The implementation is intentionally pure-Python so it can run inside the
test environment without system dependencies while still matching the
production behaviour documented in Phase 12.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, replace
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Enumeration representing the breaker state."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __str__(self) -> str:
        return self.value


@dataclass
class CircuitBreakerConfig:
    """
    Configuration for `CircuitBreaker`.

    Attributes mirror the expectations encoded in the pytest suite:
    - failure_threshold: number of consecutive handled failures before opening
    - timeout_duration: seconds to wait before probing service again
    - success_threshold: required successes in HALF_OPEN to close circuit
    - half_open_max_calls: max trial calls allowed while half-open
    - failure_rate_threshold: failure ratio (0-1) over `failure_window`
    - failure_window: sliding window (seconds) for rate calculation
    - min_calls_for_rate_check: minimum calls before considering rate opening
    - expected_exception: exception type counted as a failure
    """

    failure_threshold: int = 5
    timeout_duration: float = 60.0
    success_threshold: int = 1
    half_open_max_calls: int = 5
    failure_rate_threshold: float = 1.0
    failure_window: float = 60.0
    min_calls_for_rate_check: int = 10
    expected_exception: Type[Exception] = Exception


class CircuitBreakerOpenError(Exception):
    """Raised when a call is attempted while the breaker is open."""

    def __init__(self, breaker_name: str, timeout_remaining: float):
        self.breaker_name = breaker_name
        self.timeout_remaining = max(timeout_remaining, 0.0)
        super().__init__(
            f"Circuit breaker '{breaker_name}' is OPEN. "
            f"Retry in {self.timeout_remaining:.1f}s."
        )


class CircuitBreaker:
    """
    Circuit breaker with configurable thresholds and rate-based opening.

    The constructor accepts either a `CircuitBreakerConfig` instance or the
    legacy keyword arguments (`failure_threshold`, `timeout`, etc.) to remain
    backwards compatible with the original implementation.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        config: Optional[CircuitBreakerConfig] = None,
        *,
        failure_threshold: Optional[int] = None,
        timeout: Optional[float] = None,
        timeout_duration: Optional[float] = None,
        success_threshold: Optional[int] = None,
        half_open_max_calls: Optional[int] = None,
        failure_rate_threshold: Optional[float] = None,
        failure_window: Optional[float] = None,
        min_calls_for_rate_check: Optional[int] = None,
        expected_exception: Optional[Type[Exception]] = None,
    ):
        base_config = replace(config) if config else CircuitBreakerConfig()

        if failure_threshold is not None:
            base_config.failure_threshold = failure_threshold
        if timeout_duration is not None:
            base_config.timeout_duration = float(timeout_duration)
        elif timeout is not None:
            base_config.timeout_duration = float(timeout)
        if success_threshold is not None:
            base_config.success_threshold = success_threshold
        if half_open_max_calls is not None:
            base_config.half_open_max_calls = half_open_max_calls
        if failure_rate_threshold is not None:
            base_config.failure_rate_threshold = failure_rate_threshold
        if failure_window is not None:
            base_config.failure_window = failure_window
        if min_calls_for_rate_check is not None:
            base_config.min_calls_for_rate_check = min_calls_for_rate_check
        if expected_exception is not None:
            base_config.expected_exception = expected_exception

        self.name = name or "circuit_breaker"
        self.config = base_config

        # Mutable state guarded by `_lock`
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0  # consecutive handled failures
        self.success_count: int = 0
        self.half_open_calls: int = 0
        self.opened_at: Optional[float] = None
        self.last_failure: Optional[float] = None

        self.failure_times: List[float] = []
        self.call_history: List[Tuple[float, bool]] = []

        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute `func` under circuit breaker protection.

        The breaker enforces OPEN/HALF_OPEN behaviour before delegation and
        updates counters after execution completes.
        """
        pre_call_time = time.time()

        with self._lock:
            self._cleanup_old_failures(pre_call_time)
            self._cleanup_call_history(pre_call_time)
            timeout_remaining = self._ready_or_raise(pre_call_time)

            if timeout_remaining is not None:
                raise CircuitBreakerOpenError(self.name, timeout_remaining)

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1

        try:
            result = func(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - exercised in tests
            handled = isinstance(exc, self.config.expected_exception)
            with self._lock:
                now = time.time()
                if handled:
                    self._record_failure(now)
                else:
                    self._record_success(now)
            raise
        else:
            with self._lock:
                self._record_success(time.time())
            return result

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Allow using breaker instances directly as decorators."""

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.call(func, *args, **kwargs)

        wrapper.circuit_breaker = self  # type: ignore[attr-defined]
        return wrapper

    def reset(self) -> None:
        """Reset the breaker to a pristine CLOSED state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.half_open_calls = 0
            self.opened_at = None
            self.last_failure = None
            self.failure_times.clear()
            self.call_history.clear()

    def update_config(
        self,
        config: Optional[CircuitBreakerConfig] = None,
        **overrides: Any,
    ) -> None:
        """
        Update the breaker configuration in-place.

        Useful when the registry already created an instance but a caller
        requests a different configuration later.
        """
        new_config = replace(config) if config else replace(self.config)
        for field, value in overrides.items():
            if hasattr(new_config, field):
                setattr(new_config, field, value)
        self.config = new_config

    def get_state(self) -> Dict[str, Any]:
        """Return diagnostic information for observability."""
        with self._lock:
            now = time.time()
            self._cleanup_old_failures(now)
            self._cleanup_call_history(now)
            failures_in_window = sum(
                1 for ts in self.failure_times if self._within_window(now, ts)
            )
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure": self.last_failure,
                "opened_at": self.opened_at,
                "time_since_open": (now - self.opened_at) if self.opened_at else None,
                "failures_in_window": failures_in_window,
            }

    # ------------------------------------------------------------------ #
    # Internal helpers (locked region only)                              #
    # ------------------------------------------------------------------ #
    def _ready_or_raise(self, now: float) -> Optional[float]:
        """
        Ensure breaker is ready for execution.

        Returns:
            None if execution may proceed, otherwise timeout remaining (seconds).
        """
        if self.state == CircuitState.OPEN:
            if self.opened_at is None:
                return self.config.timeout_duration

            elapsed = now - self.opened_at
            if elapsed >= self.config.timeout_duration:
                self._transition_to_half_open(now)
            else:
                return self.config.timeout_duration - elapsed

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                elapsed = (now - self.opened_at) if self.opened_at else 0.0
                return max(self.config.timeout_duration - elapsed, 0.0)

        return None

    def _record_success(self, now: float) -> None:
        self.success_count += 1
        self.failure_count = 0
        self.call_history.append((now, True))
        self._cleanup_call_history(now)

        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self._close()
        else:
            # Success while closed clears stale failure timestamps as a safeguard
            self._cleanup_old_failures(now)

    def _record_failure(self, now: float) -> None:
        self.success_count = 0
        self.failure_count += 1
        self.last_failure = now
        self.failure_times.append(now)
        self.call_history.append((now, False))
        self._cleanup_old_failures(now)
        self._cleanup_call_history(now)

        if self.state == CircuitState.HALF_OPEN:
            self._open(now)
            return

        should_open = False
        if self.config.failure_threshold >= 0 and self.failure_count >= self.config.failure_threshold:
            should_open = True
        elif self._should_open_due_to_failure_rate(now):
            should_open = True

        if should_open:
            self._open(now)

    def _should_open_due_to_failure_rate(self, now: float) -> bool:
        if self.config.failure_rate_threshold >= 1.0:
            return False

        window_calls = [
            entry for entry in self.call_history if self._within_window(now, entry[0])
        ]
        if len(window_calls) < self.config.min_calls_for_rate_check or not window_calls:
            return False

        failures = sum(1 for _, success in window_calls if not success)
        failure_rate = failures / len(window_calls)
        return failure_rate >= self.config.failure_rate_threshold

    def _open(self, now: float) -> None:
        self.state = CircuitState.OPEN
        self.opened_at = now
        self.half_open_calls = 0
        logger.debug("[%s] Circuit opened", self.name)

    def _transition_to_half_open(self, now: float) -> None:
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        logger.debug("[%s] Circuit half-open (probing)", self.name)

    def _close(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.opened_at = None
        logger.debug("[%s] Circuit closed", self.name)

    def _cleanup_old_failures(self, now: Optional[float] = None) -> None:
        if now is None:
            now = time.time()
        window = self.config.failure_window
        if window <= 0:
            return
        self.failure_times = [ts for ts in self.failure_times if self._within_window(now, ts)]

    def _cleanup_call_history(self, now: Optional[float] = None) -> None:
        if now is None:
            now = time.time()
        window = max(self.config.failure_window, 1.0)
        self.call_history = [entry for entry in self.call_history if now - entry[0] <= window]

    def _within_window(self, now: float, timestamp: float) -> bool:
        return (now - timestamp) <= self.config.failure_window


# ---------------------------------------------------------------------- #
# Global registry / decorator helpers                                   #
# ---------------------------------------------------------------------- #
_breaker_registry: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
    **overrides: Any,
) -> CircuitBreaker:
    """Retrieve or create a named circuit breaker."""
    breaker = _breaker_registry.get(name)
    if breaker is None:
        breaker = CircuitBreaker(name=name, config=config, **overrides)
        _breaker_registry[name] = breaker
    else:
        if config or overrides:
            breaker.update_config(config, **overrides)
    return breaker


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Return a shallow copy of the breaker registry."""
    return dict(_breaker_registry)


def reset_all_circuit_breakers() -> None:
    """Reset every registered breaker."""
    for breaker in _breaker_registry.values():
        breaker.reset()


def with_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
    **overrides: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator applying (and registering) a circuit breaker around a callable.
    """
    breaker = get_circuit_breaker(name, config, **overrides)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)

        wrapper.circuit_breaker = breaker  # type: ignore[attr-defined]
        return wrapper

    return decorator


# ---------------------------------------------------------------------- #
# Predefined configurations used throughout the stack                    #
# ---------------------------------------------------------------------- #
DATABASE_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    timeout_duration=30.0,
    success_threshold=2,
    failure_rate_threshold=0.5,
    min_calls_for_rate_check=10,
)

API_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=10,
    timeout_duration=60.0,
    success_threshold=3,
    failure_rate_threshold=0.6,
    min_calls_for_rate_check=10,
)

AI_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,
    timeout_duration=90.0,
    success_threshold=2,
    half_open_max_calls=2,
    failure_rate_threshold=0.7,
    min_calls_for_rate_check=5,
    failure_window=120.0,
)


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "CircuitBreakerOpenError",
    "with_circuit_breaker",
    "get_circuit_breaker",
    "get_all_circuit_breakers",
    "reset_all_circuit_breakers",
    "DATABASE_CIRCUIT_CONFIG",
    "API_CIRCUIT_CONFIG",
    "AI_CIRCUIT_CONFIG",
]


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    logging.basicConfig(level=logging.INFO)

    breaker = CircuitBreaker("demo", failure_threshold=2, timeout_duration=2.0)

    def flaky(counter=[0]):
        counter[0] += 1
        if counter[0] < 3:
            raise RuntimeError("boom")
        return "recovered"

    for _ in range(4):
        try:
            print("Call result:", breaker.call(flaky))
        except Exception as exc:  # noqa: BLE001
            print("Call failed:", exc)
            time.sleep(0.5)

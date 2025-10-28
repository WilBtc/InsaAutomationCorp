# Phase 12 - Week 1: Error Handling Implementation Plan
**Start Date**: October 28, 2025
**Duration**: 6 days (2 days per component)
**Goal**: Implement enterprise-grade error handling for multi-agent system

---

## Overview

This week focuses on making the multi-agent system resilient to failures through three critical components:

1. **Retry Logic** (Days 1-2)
2. **Circuit Breaker** (Days 3-4)
3. **Dead Letter Queue** (Days 5-6)

---

## Component 1: Retry Logic (Days 1-2)

### Goal
Handle transient failures (network timeouts, temporary unavailability) with intelligent retry mechanisms.

### Implementation: `agent_retry.py`

```python
import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type, Tuple

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retriable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retriable_exceptions = retriable_exceptions

def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator for adding retry logic to functions.

    Usage:
        @with_retry(RetryConfig(max_attempts=5, base_delay=2.0))
        def send_message(msg):
            # Your code here
            pass
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

                    if attempt == config.max_attempts:
                        logger.error(
                            f"❌ {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )

                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt}/{config.max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)

            # Should never reach here
            raise last_exception

        return wrapper
    return decorator
```

### Integration Points

1. **Message Bus** (`agent_message_bus.py`):
   ```python
   @with_retry(RetryConfig(max_attempts=3, base_delay=0.5))
   def publish_message(self, topic: str, message: Dict[str, Any]):
       # Existing publish logic
       pass
   ```

2. **Orchestrator** (`orchestrator_agent_optimized.py`):
   ```python
   @with_retry(RetryConfig(max_attempts=5, base_delay=2.0))
   def _decompose_with_claude(self, user_query: str):
       # Existing Claude Code subprocess logic
       pass
   ```

3. **Agent Workers** (`agent_worker.py`):
   ```python
   @with_retry(RetryConfig(max_attempts=3, base_delay=1.0))
   def execute_tool(self, tool_name: str, params: Dict):
       # Existing tool execution logic
       pass
   ```

### Testing

**Test File**: `test_retry_logic.py`

```python
import pytest
import time
from agent_retry import with_retry, RetryConfig

def test_retry_success_on_second_attempt():
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

def test_retry_failure_after_max_attempts():
    """Test failure after exhausting retries"""
    call_count = 0

    @with_retry(RetryConfig(max_attempts=3, base_delay=0.1, jitter=False))
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Permanent failure")

    with pytest.raises(ValueError):
        always_fails()

    assert call_count == 3

def test_exponential_backoff():
    """Test exponential backoff delays"""
    delays = []

    @with_retry(RetryConfig(max_attempts=4, base_delay=1.0, exponential_base=2.0, jitter=False))
    def track_delays():
        start = time.time()
        if len(delays) > 0:
            delays.append(time.time() - delays[-1][1])
        delays.append((len(delays), time.time()))
        raise ValueError("Force retry")

    with pytest.raises(ValueError):
        track_delays()

    # Delays should be approximately: 1s, 2s, 4s
    # (with some tolerance for test execution time)
```

---

## Component 2: Circuit Breaker (Days 3-4)

### Goal
Prevent cascading failures by "opening" the circuit when error rate is too high, allowing systems to recover.

### State Machine
```
CLOSED (normal operation)
   ↓ (failure threshold exceeded)
OPEN (reject requests immediately)
   ↓ (timeout expires)
HALF_OPEN (test if service recovered)
   ↓ (success) → CLOSED
   ↓ (failure) → OPEN
```

### Implementation: `circuit_breaker.py`

```python
import time
import logging
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # Open after N consecutive failures
    timeout_duration: float = 60.0  # Seconds to wait before HALF_OPEN
    success_threshold: int = 2      # Successes needed to close from HALF_OPEN

class CircuitBreaker:
    """Circuit breaker to prevent cascading failures"""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""

        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"🔄 Circuit breaker '{self.name}': OPEN → HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN (opened {time.time() - self.opened_at:.0f}s ago)"
                )

        # Attempt to execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to test recovery"""
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
                self.opened_at = None

        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self, exception: Exception):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Immediate fail-back to OPEN
            logger.warning(f"⚠️ Circuit breaker '{self.name}': HALF_OPEN → OPEN (test failed)")
            self.state = CircuitState.OPEN
            self.opened_at = time.time()
            self.success_count = 0

        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                logger.error(
                    f"❌ Circuit breaker '{self.name}': CLOSED → OPEN "
                    f"({self.failure_count} consecutive failures)"
                )
                self.state = CircuitState.OPEN
                self.opened_at = time.time()

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
    """
    breaker = CircuitBreaker(name, config)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
```

### Integration Points

1. **Claude Code Subprocess** (orchestrator):
   ```python
   @with_circuit_breaker("claude_subprocess", CircuitBreakerConfig(failure_threshold=3))
   def _decompose_with_claude(self, user_query: str):
       # Subprocess call
       pass
   ```

2. **Database Connections**:
   ```python
   @with_circuit_breaker("database", CircuitBreakerConfig(failure_threshold=5, timeout_duration=30))
   def execute_query(self, query: str):
       # Database query
       pass
   ```

3. **External APIs** (MCP tools):
   ```python
   @with_circuit_breaker("erpnext_api", CircuitBreakerConfig(failure_threshold=3))
   def call_erpnext_tool(self, tool_name: str, params: Dict):
       # ERPNext MCP call
       pass
   ```

---

## Component 3: Dead Letter Queue (Days 5-6)

### Goal
Store messages that fail processing after all retries, allowing manual replay and failure analytics.

### Implementation: `dead_letter_queue.py`

```python
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DeadLetterQueue:
    """
    Dead letter queue for failed messages.
    Stores messages that couldn't be processed after retries.
    """

    def __init__(self, db_path: str = "/var/lib/insa-crm/dead_letter_queue.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize DLQ database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dead_letters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    message TEXT NOT NULL,
                    original_timestamp REAL NOT NULL,
                    failed_timestamp REAL NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'failed',
                    replayed_at REAL,
                    notes TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topic ON dead_letters(topic)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON dead_letters(status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_failed_timestamp ON dead_letters(failed_timestamp)
            """)

    def add_message(
        self,
        topic: str,
        message: Dict[str, Any],
        error: Exception,
        retry_count: int = 0
    ):
        """Add a failed message to the DLQ"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO dead_letters (
                    topic, message, original_timestamp, failed_timestamp,
                    error_type, error_message, retry_count, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                topic,
                json.dumps(message),
                message.get('timestamp', datetime.now().timestamp()),
                datetime.now().timestamp(),
                type(error).__name__,
                str(error),
                retry_count,
                'failed'
            ))

            dlq_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        logger.error(
            f"📮 Message sent to DLQ (ID: {dlq_id}) - Topic: {topic}, "
            f"Error: {type(error).__name__}: {error}"
        )

        return dlq_id

    def get_failed_messages(
        self,
        topic: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get failed messages from DLQ"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if topic:
                cursor = conn.execute("""
                    SELECT * FROM dead_letters
                    WHERE status = 'failed' AND topic = ?
                    ORDER BY failed_timestamp DESC
                    LIMIT ?
                """, (topic, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM dead_letters
                    WHERE status = 'failed'
                    ORDER BY failed_timestamp DESC
                    LIMIT ?
                """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def replay_message(self, dlq_id: int, message_bus) -> bool:
        """
        Replay a message from DLQ back to the message bus.
        Returns True if successful.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM dead_letters WHERE id = ? AND status = 'failed'",
                (dlq_id,)
            ).fetchone()

            if not row:
                logger.warning(f"⚠️ DLQ message {dlq_id} not found or already replayed")
                return False

            message = json.loads(row['message'])
            topic = row['topic']

            try:
                # Republish to message bus
                message_bus.publish_message(topic, message)

                # Mark as replayed
                conn.execute("""
                    UPDATE dead_letters
                    SET status = 'replayed', replayed_at = ?
                    WHERE id = ?
                """, (datetime.now().timestamp(), dlq_id))

                logger.info(f"✅ DLQ message {dlq_id} successfully replayed to topic '{topic}'")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to replay DLQ message {dlq_id}: {e}")
                return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get DLQ statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}

            # Total failed messages
            stats['total_failed'] = conn.execute(
                "SELECT COUNT(*) FROM dead_letters WHERE status = 'failed'"
            ).fetchone()[0]

            # Total replayed messages
            stats['total_replayed'] = conn.execute(
                "SELECT COUNT(*) FROM dead_letters WHERE status = 'replayed'"
            ).fetchone()[0]

            # Failures by topic
            cursor = conn.execute("""
                SELECT topic, COUNT(*) as count
                FROM dead_letters
                WHERE status = 'failed'
                GROUP BY topic
                ORDER BY count DESC
            """)
            stats['failures_by_topic'] = {row[0]: row[1] for row in cursor.fetchall()}

            # Failures by error type
            cursor = conn.execute("""
                SELECT error_type, COUNT(*) as count
                FROM dead_letters
                WHERE status = 'failed'
                GROUP BY error_type
                ORDER BY count DESC
            """)
            stats['failures_by_error'] = {row[0]: row[1] for row in cursor.fetchall()}

            return stats
```

### Integration with Message Bus

**Update `agent_message_bus.py`**:

```python
from dead_letter_queue import DeadLetterQueue

class AgentMessageBus:
    def __init__(self, db_path: str = "/var/lib/insa-crm/agent_messages.db"):
        # Existing init
        self.dlq = DeadLetterQueue()

    @with_retry(RetryConfig(max_attempts=3, base_delay=1.0))
    def publish_message(self, topic: str, message: Dict[str, Any]):
        try:
            # Existing publish logic
            pass
        except Exception as e:
            # After all retries failed, send to DLQ
            self.dlq.add_message(topic, message, e, retry_count=3)
            raise
```

---

## Week 1 Testing Plan

### Day 1-2: Retry Logic Tests
- Unit tests for retry decorator
- Integration tests with message bus
- Performance tests (verify delays)

### Day 3-4: Circuit Breaker Tests
- State transition tests (CLOSED → OPEN → HALF_OPEN → CLOSED)
- Integration with orchestrator
- Recovery behavior tests

### Day 5-6: Dead Letter Queue Tests
- Message storage tests
- Replay functionality tests
- Statistics and analytics tests
- End-to-end test with all components

---

## Success Criteria

By end of Week 1, we should have:

✅ **Retry Logic**:
- 95%+ success rate on transient failures
- <5s average retry delay
- Zero data loss on recoverable errors

✅ **Circuit Breaker**:
- Prevent cascading failures (test with simulated outages)
- <1min recovery time (OPEN → CLOSED)
- Clear logging of state transitions

✅ **Dead Letter Queue**:
- 100% capture of failed messages
- Replay functionality working
- Analytics showing failure patterns

---

## Next Steps (Week 2)

After completing error handling, Week 2 will focus on:
- Prometheus metrics export
- Health monitoring daemon
- Security hardening (JWT auth, rate limiting)

---

**Created**: October 28, 2025
**Status**: Ready to implement
**Owner**: INSA Automation Corp

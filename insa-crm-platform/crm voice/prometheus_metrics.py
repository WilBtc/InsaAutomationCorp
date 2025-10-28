"""
Prometheus Metrics Infrastructure for INSA CRM Platform
========================================================

Enterprise-grade metrics collection for:
- Agent request tracking (counters, histograms)
- Cache performance (hit/miss rates)
- Message bus throughput
- Worker health status
- Database operations
- Error rates and recovery

Metrics exported on port 9091 (/metrics endpoint)
Grafana dashboards: 6 panels (requests, latency, cache, workers, errors, DB)

Created: October 28, 2025
Status: Production-ready monitoring infrastructure
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    generate_latest, CollectorRegistry, REGISTRY,
    start_http_server, MetricsHandler
)
from typing import Dict, Any, Optional, Callable
import time
import functools
import threading
import logging
from contextlib import contextmanager
from http.server import HTTPServer
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# METRIC DEFINITIONS
# ============================================================================

# Request Metrics
agent_requests_total = Counter(
    'insa_agent_requests_total',
    'Total number of requests by agent type',
    ['agent_type', 'status']  # status: success, error, timeout
)

agent_request_duration_seconds = Histogram(
    'insa_agent_request_duration_seconds',
    'Request duration in seconds',
    ['agent_type'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

agent_request_size_bytes = Histogram(
    'insa_agent_request_size_bytes',
    'Request payload size in bytes',
    ['agent_type'],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000)
)

agent_response_size_bytes = Histogram(
    'insa_agent_response_size_bytes',
    'Response payload size in bytes',
    ['agent_type'],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000)
)

# Cache Metrics
cache_hits_total = Counter(
    'insa_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']  # orchestrator, pattern, session
)

cache_misses_total = Counter(
    'insa_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

cache_size_entries = Gauge(
    'insa_cache_size_entries',
    'Number of entries in cache',
    ['cache_type']
)

cache_evictions_total = Counter(
    'insa_cache_evictions_total',
    'Total number of cache evictions',
    ['cache_type', 'reason']  # reason: ttl_expired, size_limit, manual
)

# Message Bus Metrics
message_bus_messages_total = Counter(
    'insa_message_bus_messages_total',
    'Total messages sent via message bus',
    ['from_agent', 'to_agent', 'message_type']  # direct, broadcast, request, response
)

message_bus_queue_depth = Gauge(
    'insa_message_bus_queue_depth',
    'Current queue depth for agent',
    ['agent_type']
)

message_bus_processing_duration_seconds = Histogram(
    'insa_message_bus_processing_duration_seconds',
    'Time to process message',
    ['agent_type'],
    buckets=(0.001, 0.01, 0.1, 0.5, 1.0, 5.0)
)

# Worker Health Metrics
worker_health_status = Gauge(
    'insa_worker_health_status',
    'Worker health status (1=healthy, 0=unhealthy)',
    ['worker_name', 'worker_type']
)

worker_active_requests = Gauge(
    'insa_worker_active_requests',
    'Number of active requests being processed',
    ['worker_name']
)

worker_queue_size = Gauge(
    'insa_worker_queue_size',
    'Number of requests in worker queue',
    ['worker_name']
)

worker_restarts_total = Counter(
    'insa_worker_restarts_total',
    'Total number of worker restarts',
    ['worker_name', 'reason']  # crash, manual, upgrade
)

# Error Handling Metrics
retry_attempts_total = Counter(
    'insa_retry_attempts_total',
    'Total retry attempts',
    ['agent_type', 'retry_number']  # retry_number: 1, 2, 3, 4, 5
)

retry_success_total = Counter(
    'insa_retry_success_total',
    'Successful retries after failure',
    ['agent_type', 'retry_number']
)

circuit_breaker_state = Gauge(
    'insa_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['agent_type']
)

circuit_breaker_transitions_total = Counter(
    'insa_circuit_breaker_transitions_total',
    'Circuit breaker state transitions',
    ['agent_type', 'from_state', 'to_state']
)

dead_letter_queue_size = Gauge(
    'insa_dead_letter_queue_size',
    'Number of messages in dead letter queue',
    ['agent_type']
)

dead_letter_replay_total = Counter(
    'insa_dead_letter_replay_total',
    'Total dead letter replay attempts',
    ['agent_type', 'status']  # success, failure
)

# Database Metrics
database_operations_total = Counter(
    'insa_database_operations_total',
    'Total database operations',
    ['operation', 'table']  # operation: select, insert, update, delete
)

database_operation_duration_seconds = Histogram(
    'insa_database_operation_duration_seconds',
    'Database operation duration',
    ['operation', 'table'],
    buckets=(0.001, 0.01, 0.1, 0.5, 1.0, 5.0)
)

database_connection_pool_size = Gauge(
    'insa_database_connection_pool_size',
    'Current database connection pool size',
    ['database_name']
)

database_errors_total = Counter(
    'insa_database_errors_total',
    'Total database errors',
    ['operation', 'error_type']
)

# Session Metrics
active_sessions_total = Gauge(
    'insa_active_sessions_total',
    'Number of active user sessions'
)

session_duration_seconds = Histogram(
    'insa_session_duration_seconds',
    'Session duration from creation to cleanup',
    buckets=(60, 300, 600, 1800, 3600, 7200)  # 1min to 2 hours
)

session_messages_total = Counter(
    'insa_session_messages_total',
    'Total messages in session',
    ['session_type']  # user, assistant
)

session_cleanup_total = Counter(
    'insa_session_cleanup_total',
    'Total session cleanups',
    ['reason']  # timeout, manual, error
)

# System Info
system_info = Info(
    'insa_system_info',
    'System information'
)


# ============================================================================
# METRIC DECORATORS & CONTEXT MANAGERS
# ============================================================================

def track_request_metrics(agent_type: str):
    """
    Decorator to automatically track request metrics.

    Usage:
        @track_request_metrics('sizing_agent')
        def handle_request(data):
            return process(data)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                # Track request size if first arg is dict
                if args and isinstance(args[0], dict):
                    request_size = len(str(args[0]).encode('utf-8'))
                    agent_request_size_bytes.labels(agent_type=agent_type).observe(request_size)

                # Execute function
                result = func(*args, **kwargs)

                # Track response size
                if result and isinstance(result, (dict, str)):
                    response_size = len(str(result).encode('utf-8'))
                    agent_response_size_bytes.labels(agent_type=agent_type).observe(response_size)

                return result

            except TimeoutError:
                status = 'timeout'
                raise
            except Exception:
                status = 'error'
                raise
            finally:
                # Record metrics
                duration = time.time() - start_time
                agent_request_duration_seconds.labels(agent_type=agent_type).observe(duration)
                agent_requests_total.labels(agent_type=agent_type, status=status).inc()

        return wrapper
    return decorator


@contextmanager
def track_database_operation(operation: str, table: str):
    """
    Context manager to track database operation metrics.

    Usage:
        with track_database_operation('select', 'sessions'):
            rows = cursor.execute('SELECT * FROM sessions').fetchall()
    """
    start_time = time.time()
    error_occurred = False
    error_type = None

    try:
        yield
    except Exception as e:
        error_occurred = True
        error_type = type(e).__name__
        raise
    finally:
        duration = time.time() - start_time
        database_operation_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)
        database_operations_total.labels(
            operation=operation,
            table=table
        ).inc()

        if error_occurred:
            database_errors_total.labels(
                operation=operation,
                error_type=error_type
            ).inc()


@contextmanager
def track_message_processing(agent_type: str):
    """
    Context manager to track message bus processing time.

    Usage:
        with track_message_processing('sizing_agent'):
            process_message(msg)
    """
    start_time = time.time()

    try:
        yield
    finally:
        duration = time.time() - start_time
        message_bus_processing_duration_seconds.labels(
            agent_type=agent_type
        ).observe(duration)


# ============================================================================
# METRIC HELPERS
# ============================================================================

class MetricsCollector:
    """
    High-level metrics collection interface for easy integration.
    """

    @staticmethod
    def record_cache_hit(cache_type: str):
        """Record a cache hit."""
        cache_hits_total.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_cache_miss(cache_type: str):
        """Record a cache miss."""
        cache_misses_total.labels(cache_type=cache_type).inc()

    @staticmethod
    def update_cache_size(cache_type: str, size: int):
        """Update cache size gauge."""
        cache_size_entries.labels(cache_type=cache_type).set(size)

    @staticmethod
    def record_cache_eviction(cache_type: str, reason: str):
        """Record a cache eviction."""
        cache_evictions_total.labels(cache_type=cache_type, reason=reason).inc()

    @staticmethod
    def record_message_sent(from_agent: str, to_agent: str, message_type: str):
        """Record a message sent via message bus."""
        message_bus_messages_total.labels(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type
        ).inc()

    @staticmethod
    def update_queue_depth(agent_type: str, depth: int):
        """Update message queue depth."""
        message_bus_queue_depth.labels(agent_type=agent_type).set(depth)

    @staticmethod
    def update_worker_health(worker_name: str, worker_type: str, is_healthy: bool):
        """Update worker health status."""
        worker_health_status.labels(
            worker_name=worker_name,
            worker_type=worker_type
        ).set(1 if is_healthy else 0)

    @staticmethod
    def update_active_requests(worker_name: str, count: int):
        """Update active request count for worker."""
        worker_active_requests.labels(worker_name=worker_name).set(count)

    @staticmethod
    def update_worker_queue(worker_name: str, size: int):
        """Update worker queue size."""
        worker_queue_size.labels(worker_name=worker_name).set(size)

    @staticmethod
    def record_worker_restart(worker_name: str, reason: str):
        """Record a worker restart."""
        worker_restarts_total.labels(worker_name=worker_name, reason=reason).inc()

    @staticmethod
    def record_retry_attempt(agent_type: str, retry_number: int):
        """Record a retry attempt."""
        retry_attempts_total.labels(
            agent_type=agent_type,
            retry_number=str(retry_number)
        ).inc()

    @staticmethod
    def record_retry_success(agent_type: str, retry_number: int):
        """Record a successful retry."""
        retry_success_total.labels(
            agent_type=agent_type,
            retry_number=str(retry_number)
        ).inc()

    @staticmethod
    def update_circuit_breaker_state(agent_type: str, state: str):
        """Update circuit breaker state (closed=0, open=1, half_open=2)."""
        state_map = {'closed': 0, 'open': 1, 'half_open': 2}
        circuit_breaker_state.labels(agent_type=agent_type).set(state_map.get(state, 0))

    @staticmethod
    def record_circuit_breaker_transition(agent_type: str, from_state: str, to_state: str):
        """Record a circuit breaker state transition."""
        circuit_breaker_transitions_total.labels(
            agent_type=agent_type,
            from_state=from_state,
            to_state=to_state
        ).inc()

    @staticmethod
    def update_dead_letter_queue_size(agent_type: str, size: int):
        """Update dead letter queue size."""
        dead_letter_queue_size.labels(agent_type=agent_type).set(size)

    @staticmethod
    def record_dead_letter_replay(agent_type: str, success: bool):
        """Record a dead letter replay attempt."""
        status = 'success' if success else 'failure'
        dead_letter_replay_total.labels(agent_type=agent_type, status=status).inc()

    @staticmethod
    def update_active_sessions(count: int):
        """Update active session count."""
        active_sessions_total.set(count)

    @staticmethod
    def record_session_duration(duration_seconds: float):
        """Record a session duration."""
        session_duration_seconds.observe(duration_seconds)

    @staticmethod
    def record_session_message(session_type: str):
        """Record a session message."""
        session_messages_total.labels(session_type=session_type).inc()

    @staticmethod
    def record_session_cleanup(reason: str):
        """Record a session cleanup."""
        session_cleanup_total.labels(reason=reason).inc()

    @staticmethod
    def update_db_pool_size(database_name: str, size: int):
        """Update database connection pool size."""
        database_connection_pool_size.labels(database_name=database_name).set(size)

    @staticmethod
    def set_system_info(version: str, environment: str, platform: str):
        """Set system information."""
        system_info.info({
            'version': version,
            'environment': environment,
            'platform': platform
        })


# ============================================================================
# METRICS SERVER
# ============================================================================

class MetricsServer:
    """
    HTTP server for Prometheus metrics scraping.
    Runs on port 9091, exposes /metrics endpoint.
    """

    def __init__(self, port: int = 9091):
        self.port = port
        self.server = None
        self.thread = None
        self._running = False

    def start(self):
        """Start the metrics server in background thread."""
        if self._running:
            logger.warning("Metrics server already running")
            return

        try:
            # Start HTTP server
            start_http_server(self.port)
            self._running = True
            logger.info(f"Prometheus metrics server started on port {self.port}")
            logger.info(f"Metrics available at: http://localhost:{self.port}/metrics")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise

    def stop(self):
        """Stop the metrics server."""
        self._running = False
        logger.info("Metrics server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

# Global metrics collector
metrics = MetricsCollector()

# Global metrics server (lazy initialization)
_metrics_server: Optional[MetricsServer] = None


def start_metrics_server(port: int = 9091):
    """Start the global metrics server."""
    global _metrics_server

    if _metrics_server is None:
        _metrics_server = MetricsServer(port=port)

    _metrics_server.start()


def stop_metrics_server():
    """Stop the global metrics server."""
    global _metrics_server

    if _metrics_server:
        _metrics_server.stop()


def get_metrics_text() -> str:
    """Get current metrics in Prometheus text format."""
    return generate_latest(REGISTRY).decode('utf-8')


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_metrics(version: str = '1.0.0', environment: str = 'production'):
    """
    Initialize metrics system with system information.

    Args:
        version: Application version
        environment: Environment (production, staging, dev)
    """
    import platform

    metrics.set_system_info(
        version=version,
        environment=environment,
        platform=platform.system()
    )

    logger.info(f"Metrics initialized: version={version}, environment={environment}")


if __name__ == '__main__':
    # Example usage
    initialize_metrics(version='1.0.0', environment='production')
    start_metrics_server(port=9091)

    # Simulate some metrics
    metrics.record_cache_hit('orchestrator')
    metrics.record_cache_miss('pattern')
    metrics.update_worker_health('sizing_agent', 'agent_worker', True)
    metrics.record_retry_attempt('sizing_agent', 1)

    print(f"\nMetrics server running on http://localhost:9091/metrics")
    print("\nSample metrics:")
    print(get_metrics_text()[:500])

    # Keep server running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_metrics_server()
        print("\nMetrics server stopped")

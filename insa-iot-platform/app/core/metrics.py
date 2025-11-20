"""
Prometheus Metrics Exporter for the Alkhorayef ESP IoT Platform.

This module provides comprehensive metrics collection for monitoring
application performance, database health, telemetry ingestion, and system resources.
"""

import time
import psutil
from typing import Dict, Any, Optional
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from app.core import get_logger, get_config


logger = get_logger(__name__)


# ============================================================================
# Prometheus Registry and Collectors
# ============================================================================

# Use the default registry for all metrics
REGISTRY = CollectorRegistry(auto_describe=True)


# ============================================================================
# Application Info Metrics
# ============================================================================

app_info = Info(
    "alkhorayef_esp_platform",
    "Application information",
    registry=REGISTRY
)


# ============================================================================
# HTTP Request Metrics
# ============================================================================

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
    registry=REGISTRY
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
    registry=REGISTRY
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=REGISTRY
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=REGISTRY
)


# ============================================================================
# Database Metrics
# ============================================================================

db_queries_total = Counter(
    "db_queries_total",
    "Total number of database queries",
    ["operation"],
    registry=REGISTRY
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=REGISTRY
)

db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
    registry=REGISTRY
)

db_connection_errors_total = Counter(
    "db_connection_errors_total",
    "Total number of database connection errors",
    registry=REGISTRY
)

db_query_errors_total = Counter(
    "db_query_errors_total",
    "Total number of database query errors",
    ["operation"],
    registry=REGISTRY
)


# ============================================================================
# Telemetry Metrics
# ============================================================================

telemetry_ingestion_total = Counter(
    "telemetry_ingestion_total",
    "Total number of telemetry records ingested",
    ["well_id", "source"],
    registry=REGISTRY
)

telemetry_ingestion_rate = Gauge(
    "telemetry_ingestion_rate",
    "Current telemetry ingestion rate (records/second)",
    registry=REGISTRY
)

telemetry_validation_errors_total = Counter(
    "telemetry_validation_errors_total",
    "Total number of telemetry validation errors",
    ["error_type"],
    registry=REGISTRY
)

telemetry_processing_duration_seconds = Histogram(
    "telemetry_processing_duration_seconds",
    "Telemetry record processing duration in seconds",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5),
    registry=REGISTRY
)


# ============================================================================
# Diagnostic Analysis Metrics
# ============================================================================

diagnostics_analysis_total = Counter(
    "diagnostics_analysis_total",
    "Total number of diagnostic analyses performed",
    ["well_id", "analysis_type"],
    registry=REGISTRY
)

diagnostics_analysis_duration_seconds = Histogram(
    "diagnostics_analysis_duration_seconds",
    "Diagnostic analysis duration in seconds",
    ["analysis_type"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY
)

diagnostics_anomalies_detected_total = Counter(
    "diagnostics_anomalies_detected_total",
    "Total number of anomalies detected",
    ["well_id", "anomaly_type"],
    registry=REGISTRY
)


# ============================================================================
# Backup System Metrics
# ============================================================================

backup_operations_total = Counter(
    "backup_operations_total",
    "Total number of backup operations",
    ["backup_type", "status"],
    registry=REGISTRY
)

backup_duration_seconds = Histogram(
    "backup_duration_seconds",
    "Backup operation duration in seconds",
    ["backup_type"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0),
    registry=REGISTRY
)

backup_size_bytes = Gauge(
    "backup_size_bytes",
    "Size of last backup in bytes",
    ["backup_type"],
    registry=REGISTRY
)

backup_last_success_timestamp = Gauge(
    "backup_last_success_timestamp",
    "Timestamp of last successful backup",
    ["backup_type"],
    registry=REGISTRY
)


# ============================================================================
# TimescaleDB Metrics
# ============================================================================

timescaledb_hypertable_chunks_total = Gauge(
    "timescaledb_hypertable_chunks_total",
    "Total number of chunks in hypertables",
    ["hypertable"],
    registry=REGISTRY
)

timescaledb_compression_ratio = Gauge(
    "timescaledb_compression_ratio",
    "Compression ratio of hypertables",
    ["hypertable"],
    registry=REGISTRY
)

timescaledb_continuous_aggregates_total = Gauge(
    "timescaledb_continuous_aggregates_total",
    "Total number of continuous aggregates",
    registry=REGISTRY
)

timescaledb_query_cache_hit_rate = Gauge(
    "timescaledb_query_cache_hit_rate",
    "Query cache hit rate (0-1)",
    registry=REGISTRY
)


# ============================================================================
# Real-Time Streaming Metrics
# ============================================================================

websocket_connections = Gauge(
    "websocket_connections",
    "Number of active WebSocket connections",
    ["status"],
    registry=REGISTRY
)

websocket_messages = Counter(
    "websocket_messages_total",
    "Total number of WebSocket messages sent",
    ["message_type", "well_id"],
    registry=REGISTRY
)

websocket_errors = Counter(
    "websocket_errors_total",
    "Total number of WebSocket errors",
    ["error_type"],
    registry=REGISTRY
)

websocket_subscriptions = Gauge(
    "websocket_subscriptions",
    "Number of active WebSocket subscriptions",
    ["well_id"],
    registry=REGISTRY
)

sse_connections = Gauge(
    "sse_connections",
    "Number of active SSE connections",
    ["well_id"],
    registry=REGISTRY
)

sse_messages = Counter(
    "sse_messages_total",
    "Total number of SSE messages sent",
    ["message_type", "well_id"],
    registry=REGISTRY
)

sse_errors = Counter(
    "sse_errors_total",
    "Total number of SSE errors",
    ["error_type"],
    registry=REGISTRY
)

realtime_publishes = Counter(
    "realtime_publishes_total",
    "Total number of real-time publishes",
    ["publish_type", "well_id"],
    registry=REGISTRY
)

realtime_publish_errors = Counter(
    "realtime_publish_errors_total",
    "Total number of real-time publish errors",
    ["publish_type", "error_type"],
    registry=REGISTRY
)

realtime_publish_duration = Histogram(
    "realtime_publish_duration_seconds",
    "Real-time publish duration in seconds",
    ["publish_type"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=REGISTRY
)


# ============================================================================
# System Resource Metrics
# ============================================================================

system_cpu_usage_percent = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage",
    registry=REGISTRY
)

system_memory_usage_percent = Gauge(
    "system_memory_usage_percent",
    "System memory usage percentage",
    registry=REGISTRY
)

system_memory_available_bytes = Gauge(
    "system_memory_available_bytes",
    "Available system memory in bytes",
    registry=REGISTRY
)

system_disk_usage_percent = Gauge(
    "system_disk_usage_percent",
    "System disk usage percentage",
    ["mount_point"],
    registry=REGISTRY
)

system_disk_available_bytes = Gauge(
    "system_disk_available_bytes",
    "Available disk space in bytes",
    ["mount_point"],
    registry=REGISTRY
)

system_network_bytes_sent = Counter(
    "system_network_bytes_sent",
    "Total network bytes sent",
    registry=REGISTRY
)

system_network_bytes_received = Counter(
    "system_network_bytes_received",
    "Total network bytes received",
    registry=REGISTRY
)


# ============================================================================
# Metrics Collection Functions
# ============================================================================

def initialize_metrics() -> None:
    """
    Initialize application metrics with static information.

    This should be called once during application startup.
    """
    config = get_config()

    app_info.info({
        "version": config.version,
        "environment": config.environment,
        "app_name": config.app_name,
    })

    logger.info("Prometheus metrics initialized")


def collect_system_metrics() -> Dict[str, Any]:
    """
    Collect current system resource metrics.

    Returns:
        Dictionary containing current system metrics
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_cpu_usage_percent.set(cpu_percent)

        # Memory metrics
        memory = psutil.virtual_memory()
        system_memory_usage_percent.set(memory.percent)
        system_memory_available_bytes.set(memory.available)

        # Disk metrics
        disk = psutil.disk_usage("/")
        system_disk_usage_percent.labels(mount_point="/").set(disk.percent)
        system_disk_available_bytes.labels(mount_point="/").set(disk.free)

        # Network metrics
        network = psutil.net_io_counters()
        system_network_bytes_sent.inc(network.bytes_sent)
        system_network_bytes_received.inc(network.bytes_recv)

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_available_gb": disk.free / (1024**3),
        }

    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        return {}


def collect_database_metrics(db_pool) -> Dict[str, Any]:
    """
    Collect database-specific metrics from TimescaleDB.

    Args:
        db_pool: Database connection pool

    Returns:
        Dictionary containing database metrics
    """
    metrics = {}

    try:
        # Get active connections
        result = db_pool.execute_query(
            """
            SELECT count(*)
            FROM pg_stat_activity
            WHERE state = 'active'
            """,
            fetch=True
        )
        if result:
            active_connections = result[0][0]
            db_connections_active.set(active_connections)
            metrics["active_connections"] = active_connections

        # Get hypertable chunk counts
        result = db_pool.execute_query(
            """
            SELECT hypertable_name, count(*) as chunk_count
            FROM timescaledb_information.chunks
            GROUP BY hypertable_name
            """,
            fetch=True
        )
        if result:
            for row in result:
                hypertable_name, chunk_count = row
                timescaledb_hypertable_chunks_total.labels(
                    hypertable=hypertable_name
                ).set(chunk_count)
                metrics[f"{hypertable_name}_chunks"] = chunk_count

        # Get compression ratio
        result = db_pool.execute_query(
            """
            SELECT
                hypertable_name,
                CASE
                    WHEN before_compression_total_bytes > 0
                    THEN before_compression_total_bytes::float /
                         NULLIF(after_compression_total_bytes, 0)::float
                    ELSE 0
                END as compression_ratio
            FROM timescaledb_information.compression_settings cs
            JOIN timescaledb_information.hypertables h
                ON cs.hypertable_schema = h.hypertable_schema
                AND cs.hypertable_name = h.hypertable_name
            LEFT JOIN (
                SELECT
                    hypertable_name,
                    sum(before_compression_total_bytes) as before_compression_total_bytes,
                    sum(after_compression_total_bytes) as after_compression_total_bytes
                FROM timescaledb_information.compressed_chunk_stats
                GROUP BY hypertable_name
            ) stats ON h.hypertable_name = stats.hypertable_name
            """,
            fetch=True
        )
        if result:
            for row in result:
                if len(row) >= 2 and row[1] is not None:
                    hypertable_name, compression_ratio = row[0], row[1]
                    timescaledb_compression_ratio.labels(
                        hypertable=hypertable_name
                    ).set(float(compression_ratio))
                    metrics[f"{hypertable_name}_compression_ratio"] = float(compression_ratio)

        # Get continuous aggregate count
        result = db_pool.execute_query(
            """
            SELECT count(*)
            FROM timescaledb_information.continuous_aggregates
            """,
            fetch=True
        )
        if result:
            cagg_count = result[0][0]
            timescaledb_continuous_aggregates_total.set(cagg_count)
            metrics["continuous_aggregates_count"] = cagg_count

    except Exception as e:
        logger.error(f"Error collecting database metrics: {e}")
        db_connection_errors_total.inc()

    return metrics


# ============================================================================
# Decorator for Tracking Function Metrics
# ============================================================================

def track_time(metric_histogram, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to track execution time of a function.

    Args:
        metric_histogram: Prometheus Histogram metric to record duration
        labels: Optional labels to apply to the metric

    Example:
        @track_time(db_query_duration_seconds, {"operation": "insert"})
        def insert_telemetry(data):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric_histogram.labels(**labels).observe(duration)
                else:
                    metric_histogram.observe(duration)
        return wrapper
    return decorator


def track_counter(metric_counter, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to increment a counter when a function is called.

    Args:
        metric_counter: Prometheus Counter metric to increment
        labels: Optional labels to apply to the metric

    Example:
        @track_counter(telemetry_ingestion_total, {"source": "esp_api"})
        def ingest_telemetry(data):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if labels:
                    metric_counter.labels(**labels).inc()
                else:
                    metric_counter.inc()
                return result
            except Exception as e:
                # Don't increment counter on error
                raise e
        return wrapper
    return decorator


# ============================================================================
# Metrics Export
# ============================================================================

def generate_metrics() -> bytes:
    """
    Generate Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format
    """
    # Collect latest system metrics before generating
    collect_system_metrics()

    return generate_latest(REGISTRY)


def get_metrics_content_type() -> str:
    """
    Get the content type for Prometheus metrics.

    Returns:
        Content type string
    """
    return CONTENT_TYPE_LATEST

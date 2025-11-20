"""
Monitoring Middleware for the Alkhorayef ESP IoT Platform.

This middleware tracks HTTP request/response metrics for Prometheus monitoring.
"""

import time
from typing import Callable
from flask import Request, Response, request, g

from app.core import get_logger
from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress,
    http_request_size_bytes,
    http_response_size_bytes,
)


logger = get_logger(__name__)


def setup_monitoring_middleware(app) -> None:
    """
    Setup monitoring middleware for Flask application.

    This configures before_request and after_request hooks to track
    HTTP request metrics.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def before_request_monitoring():
        """
        Track request start time and increment in-progress counter.
        """
        # Skip metrics endpoint to avoid recursive metrics collection
        if request.path == "/metrics":
            return

        # Store request start time in Flask's g object
        g.start_time = time.time()

        # Get endpoint and method
        endpoint = request.endpoint or "unknown"
        method = request.method

        # Increment in-progress counter
        http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).inc()

        # Track request size
        content_length = request.content_length
        if content_length:
            http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(content_length)

    @app.after_request
    def after_request_monitoring(response: Response) -> Response:
        """
        Track request completion metrics.

        Args:
            response: Flask response object

        Returns:
            Unmodified response object
        """
        # Skip metrics endpoint to avoid recursive metrics collection
        if request.path == "/metrics":
            return response

        # Get endpoint and method
        endpoint = request.endpoint or "unknown"
        method = request.method
        status = response.status_code

        # Decrement in-progress counter
        http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).dec()

        # Track total requests
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()

        # Track request duration
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

        # Track response size
        content_length = response.content_length
        if content_length:
            http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(content_length)

        return response

    @app.teardown_request
    def teardown_request_monitoring(exception=None):
        """
        Cleanup in-progress metrics on request teardown.

        This handles cases where requests fail before after_request.

        Args:
            exception: Exception that occurred during request processing, if any
        """
        # Skip metrics endpoint
        if request.path == "/metrics":
            return

        # If there was an exception and the in-progress counter wasn't decremented
        # (after_request didn't run), decrement it here
        if exception is not None:
            endpoint = request.endpoint or "unknown"
            method = request.method

            # Check if we still have start_time (meaning after_request didn't run)
            if hasattr(g, "start_time"):
                http_requests_in_progress.labels(
                    method=method,
                    endpoint=endpoint
                ).dec()

                # Track failed requests
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=500
                ).inc()

                # Log the error
                logger.error(
                    f"Request failed: {method} {endpoint}",
                    exc_info=exception
                )

    logger.info("Monitoring middleware configured")


def get_request_stats() -> dict:
    """
    Get current request statistics.

    This is a helper function to retrieve request metrics
    for health checks and debugging.

    Returns:
        Dictionary containing request statistics
    """
    # Note: This is a simplified version.
    # In production, you might want to query the actual Prometheus metrics
    # or maintain separate counters for real-time stats.

    return {
        "monitoring": "active",
        "tracked_metrics": [
            "http_requests_total",
            "http_request_duration_seconds",
            "http_requests_in_progress",
            "http_request_size_bytes",
            "http_response_size_bytes"
        ]
    }

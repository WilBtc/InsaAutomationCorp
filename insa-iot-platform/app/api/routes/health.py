"""
Health check endpoints for the Alkhorayef ESP IoT Platform.

This module provides Kubernetes-style health check endpoints
for liveness and readiness probes, plus comprehensive health metrics.
"""

from datetime import datetime
from typing import Dict, Any
import psutil

from flask import Blueprint, jsonify, Response

from app.core import get_logger, get_config
from app.db import get_db_pool
from app.core.metrics import (
    generate_metrics,
    get_metrics_content_type,
    collect_system_metrics,
    collect_database_metrics,
)


logger = get_logger(__name__)
health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.route("/live", methods=["GET"])
def liveness() -> Response:
    """
    Liveness probe endpoint.

    This endpoint checks if the application is running.
    It should return 200 if the process is alive, regardless of dependency health.

    Returns:
        JSON response with liveness status
    """
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "alkhorayef-esp-iot-platform"
    }), 200


@health_bp.route("/ready", methods=["GET"])
def readiness() -> Response:
    """
    Readiness probe endpoint.

    This endpoint checks if the application is ready to serve traffic.
    It verifies that all critical dependencies are available.

    Returns:
        JSON response with readiness status and dependency health
    """
    config = get_config()
    health_status: Dict[str, Any] = {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "alkhorayef-esp-iot-platform",
        "version": config.version,
        "environment": config.environment,
        "dependencies": {}
    }

    overall_healthy = True

    # Check database connectivity
    try:
        db_pool = get_db_pool()
        result = db_pool.execute_query("SELECT 1", fetch=True)
        if result and result[0][0] == 1:
            health_status["dependencies"]["database"] = {
                "status": "healthy",
                "type": "postgresql"
            }
        else:
            overall_healthy = False
            health_status["dependencies"]["database"] = {
                "status": "unhealthy",
                "type": "postgresql",
                "error": "Query returned unexpected result"
            }
    except Exception as e:
        overall_healthy = False
        health_status["dependencies"]["database"] = {
            "status": "unhealthy",
            "type": "postgresql",
            "error": str(e)
        }
        logger.error(
            "Database health check failed",
            exc_info=e
        )

    # Check TimescaleDB extension
    try:
        db_pool = get_db_pool()
        result = db_pool.execute_query(
            "SELECT extname FROM pg_extension WHERE extname = 'timescaledb'",
            fetch=True
        )
        if result and len(result) > 0:
            health_status["dependencies"]["timescaledb"] = {
                "status": "healthy"
            }
        else:
            health_status["dependencies"]["timescaledb"] = {
                "status": "warning",
                "message": "TimescaleDB extension not found"
            }
    except Exception as e:
        logger.error(f"TimescaleDB check failed: {e}")
        health_status["dependencies"]["timescaledb"] = {
            "status": "error",
            "error": str(e)
        }

    # Set overall status
    if not overall_healthy:
        health_status["status"] = "not_ready"
        return jsonify(health_status), 503

    return jsonify(health_status), 200


@health_bp.route("/startup", methods=["GET"])
def startup() -> Response:
    """
    Startup probe endpoint.

    This endpoint checks if the application has completed initialization.
    Used for slow-starting containers.

    Returns:
        JSON response with startup status
    """
    try:
        # Check if database pool is initialized
        db_pool = get_db_pool()

        # Verify database tables exist
        result = db_pool.execute_query(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'esp_telemetry'
            )
            """,
            fetch=True
        )

        tables_exist = result[0][0] if result else False

        if tables_exist:
            return jsonify({
                "status": "started",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Application started successfully"
            }), 200
        else:
            return jsonify({
                "status": "starting",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Database tables not yet initialized"
            }), 503

    except Exception as e:
        logger.error(
            "Startup check failed",
            exc_info=e
        )
        return jsonify({
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }), 503


@health_bp.route("", methods=["GET"])
@health_bp.route("/", methods=["GET"])
def health() -> Response:
    """
    General health check endpoint.

    Convenience endpoint that combines liveness and readiness checks.

    Returns:
        JSON response with overall health status
    """
    return readiness()


@health_bp.route("/detailed", methods=["GET"])
def detailed_health() -> Response:
    """
    Detailed health check endpoint with system metrics.

    This endpoint provides comprehensive health information including:
    - Database connectivity and TimescaleDB features
    - System resources (CPU, memory, disk)
    - Hypertable status
    - Continuous aggregates status

    Returns:
        JSON response with detailed health information
    """
    config = get_config()
    health_data: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "alkhorayef-esp-iot-platform",
        "version": config.version,
        "environment": config.environment,
        "components": {}
    }

    overall_healthy = True

    # Database connectivity check
    try:
        db_pool = get_db_pool()
        result = db_pool.execute_query("SELECT version()", fetch=True)
        if result:
            health_data["components"]["database"] = {
                "status": "healthy",
                "type": "postgresql",
                "version": result[0][0].split(",")[0]
            }
        else:
            overall_healthy = False
            health_data["components"]["database"] = {
                "status": "unhealthy",
                "error": "Unable to query version"
            }
    except Exception as e:
        overall_healthy = False
        health_data["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # TimescaleDB extension check
    try:
        db_pool = get_db_pool()
        result = db_pool.execute_query(
            "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'",
            fetch=True
        )
        if result:
            health_data["components"]["timescaledb"] = {
                "status": "healthy",
                "version": result[0][0]
            }
        else:
            health_data["components"]["timescaledb"] = {
                "status": "not_installed"
            }
    except Exception as e:
        health_data["components"]["timescaledb"] = {
            "status": "error",
            "error": str(e)
        }

    # Hypertable status check
    try:
        db_pool = get_db_pool()
        result = db_pool.execute_query(
            """
            SELECT
                hypertable_name,
                num_chunks
            FROM timescaledb_information.hypertables
            """,
            fetch=True
        )
        if result:
            hypertables = [
                {"name": row[0], "chunks": row[1]}
                for row in result
            ]
            health_data["components"]["hypertables"] = {
                "status": "healthy",
                "count": len(hypertables),
                "tables": hypertables
            }
        else:
            health_data["components"]["hypertables"] = {
                "status": "none",
                "count": 0
            }
    except Exception as e:
        health_data["components"]["hypertables"] = {
            "status": "error",
            "error": str(e)
        }

    # Continuous aggregates check
    try:
        db_pool = get_db_pool()
        result = db_pool.execute_query(
            """
            SELECT
                view_name,
                materialized_only
            FROM timescaledb_information.continuous_aggregates
            """,
            fetch=True
        )
        if result:
            caggs = [
                {"name": row[0], "materialized_only": row[1]}
                for row in result
            ]
            health_data["components"]["continuous_aggregates"] = {
                "status": "healthy",
                "count": len(caggs),
                "aggregates": caggs
            }
        else:
            health_data["components"]["continuous_aggregates"] = {
                "status": "none",
                "count": 0
            }
    except Exception as e:
        health_data["components"]["continuous_aggregates"] = {
            "status": "error",
            "error": str(e)
        }

    # System resources
    try:
        system_metrics = collect_system_metrics()
        health_data["components"]["system_resources"] = {
            "status": "healthy",
            "cpu_percent": system_metrics.get("cpu_percent", 0),
            "memory_percent": system_metrics.get("memory_percent", 0),
            "memory_available_gb": system_metrics.get("memory_available_gb", 0),
            "disk_percent": system_metrics.get("disk_percent", 0),
            "disk_available_gb": system_metrics.get("disk_available_gb", 0)
        }

        # Check for resource warnings
        if system_metrics.get("memory_percent", 0) > 80:
            health_data["components"]["system_resources"]["warning"] = "High memory usage"
        if system_metrics.get("disk_percent", 0) > 90:
            health_data["components"]["system_resources"]["warning"] = "Low disk space"

    except Exception as e:
        health_data["components"]["system_resources"] = {
            "status": "error",
            "error": str(e)
        }

    # Database metrics
    try:
        db_metrics = collect_database_metrics(db_pool)
        health_data["components"]["database_metrics"] = {
            "status": "healthy",
            "active_connections": db_metrics.get("active_connections", 0),
            "continuous_aggregates_count": db_metrics.get("continuous_aggregates_count", 0)
        }
    except Exception as e:
        health_data["components"]["database_metrics"] = {
            "status": "error",
            "error": str(e)
        }

    # Set overall status
    if not overall_healthy:
        health_data["status"] = "degraded"

    return jsonify(health_data), 200 if overall_healthy else 503


@health_bp.route("/metrics", methods=["GET"])
def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    This endpoint exposes application metrics in Prometheus format.

    Returns:
        Prometheus metrics in text format
    """
    try:
        metrics_data = generate_metrics()
        return Response(
            metrics_data,
            mimetype=get_metrics_content_type()
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            f"# Error generating metrics: {str(e)}\n",
            mimetype="text/plain",
            status=500
        )

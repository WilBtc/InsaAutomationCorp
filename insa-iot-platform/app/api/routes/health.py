"""
Health check endpoints for the Alkhorayef ESP IoT Platform.

This module provides Kubernetes-style health check endpoints
for liveness and readiness probes.
"""

from datetime import datetime
from typing import Dict, Any

from flask import Blueprint, jsonify, Response

from app.core import get_logger, get_config
from app.db import get_db_pool


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

    # Check database
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

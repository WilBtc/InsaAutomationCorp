"""
Alkhorayef ESP IoT Platform - Main Application Module

This module provides the Flask application factory for creating and configuring
the ESP IoT platform application.
"""

from typing import Optional
from flask import Flask, jsonify

from app.core import get_config, setup_logging, get_logger
from app.db import get_db_pool, SQL_CREATE_TABLES
from app.api import (
    health_bp,
    telemetry_bp,
    diagnostics_bp,
    register_error_handlers,
    register_response_handlers
)


def create_app(config_override: Optional[dict] = None) -> Flask:
    """
    Application factory for creating Flask app instances.

    This factory pattern allows for:
    - Multiple app instances with different configurations
    - Easier testing with mock configurations
    - Better separation of concerns
    - Cleaner initialization process

    Args:
        config_override: Optional configuration overrides

    Returns:
        Configured Flask application instance
    """
    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    config = get_config()

    # Override config if provided (mainly for testing)
    if config_override:
        for key, value in config_override.items():
            setattr(config, key, value)

    # Set Flask config
    app.config["APP_NAME"] = config.app_name
    app.config["VERSION"] = config.version
    app.config["DEBUG"] = config.debug
    app.config["ENVIRONMENT"] = config.environment
    app.config["JSON_SORT_KEYS"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = not config.is_production

    # Setup logging
    logger = setup_logging("alkhorayef-esp-platform")
    logger.info(
        f"Initializing {config.app_name} v{config.version}",
        extra={
            "extra_fields": {
                "environment": config.environment,
                "debug": config.debug
            }
        }
    )

    # Initialize database
    with app.app_context():
        try:
            db_pool = get_db_pool()
            logger.info("Database connection pool initialized")

            # Create tables if they don't exist
            db_pool.execute_query(SQL_CREATE_TABLES, fetch=False)
            logger.info("Database tables verified/created")

        except Exception as e:
            logger.critical(
                "Failed to initialize database",
                exc_info=e
            )
            raise

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(diagnostics_bp)
    logger.info("API routes registered")

    # Register error handlers
    register_error_handlers(app)
    register_response_handlers(app)
    logger.info("Error handlers registered")

    # Root endpoint
    @app.route("/")
    def root():
        """Root endpoint with API information."""
        return jsonify({
            "name": config.app_name,
            "version": config.version,
            "environment": config.environment,
            "api_version": "v1",
            "endpoints": {
                "health": "/health",
                "telemetry": "/api/v1/telemetry",
                "diagnostics": "/api/v1/diagnostics"
            },
            "documentation": "/api/v1/docs"  # Future: OpenAPI/Swagger docs
        })

    # API documentation placeholder
    @app.route("/api/v1/docs")
    def api_docs():
        """API documentation endpoint (placeholder for OpenAPI/Swagger)."""
        return jsonify({
            "message": "API documentation coming soon",
            "openapi_version": "3.0.0",
            "endpoints": {
                "health_checks": {
                    "GET /health": "General health check",
                    "GET /health/live": "Liveness probe",
                    "GET /health/ready": "Readiness probe",
                    "GET /health/startup": "Startup probe"
                },
                "telemetry": {
                    "POST /api/v1/telemetry/ingest": "Ingest single telemetry reading",
                    "POST /api/v1/telemetry/batch": "Ingest batch of telemetry readings",
                    "GET /api/v1/telemetry/wells/<well_id>/latest": "Get latest telemetry",
                    "GET /api/v1/telemetry/wells/<well_id>/history": "Get telemetry history",
                    "GET /api/v1/telemetry/wells/<well_id>/summary": "Get well summary"
                },
                "diagnostics": {
                    "POST /api/v1/diagnostics/analyze": "Analyze telemetry data",
                    "POST /api/v1/diagnostics/wells/<well_id>/analyze-latest": "Analyze latest telemetry",
                    "GET /api/v1/diagnostics/wells/<well_id>/history": "Get diagnostic history",
                    "GET /api/v1/diagnostics/critical": "Get critical diagnostics"
                }
            }
        })

    logger.info(
        f"{config.app_name} initialization complete",
        extra={
            "extra_fields": {
                "environment": config.environment,
                "version": config.version
            }
        }
    )

    return app


def cleanup_resources() -> None:
    """
    Cleanup application resources.

    This function should be called when the application is shutting down
    to properly close database connections and other resources.
    """
    from app.db import close_db_pool

    logger = get_logger(__name__)
    logger.info("Cleaning up application resources")

    try:
        close_db_pool()
        logger.info("Database pool closed")
    except Exception as e:
        logger.error("Error closing database pool", exc_info=e)

    logger.info("Application cleanup complete")


# Note: Do NOT create app instance at module level to avoid import-time initialization
# Create app instance on demand using create_app() when needed
# For WSGI servers: use app = create_app() in your WSGI file
# For direct execution: see __main__ block below


if __name__ == "__main__":
    """
    Run the application directly (development only).

    For production, use a proper WSGI server like gunicorn:
        gunicorn -w 4 -b 0.0.0.0:8000 app:app
    """
    config = get_config()

    if config.is_production:
        print("WARNING: Running Flask development server in production is not recommended!")
        print("Use a production WSGI server like gunicorn instead.")

    try:
        app.run(
            host=config.host,
            port=config.port,
            debug=config.debug
        )
    finally:
        cleanup_resources()

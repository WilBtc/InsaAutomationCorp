"""
Error handling middleware for the Alkhorayef ESP IoT Platform.

This module provides global error handling for Flask application.
"""

from typing import Tuple
from flask import Flask, jsonify, Response
from werkzeug.exceptions import HTTPException

from app.core import (
    get_logger,
    PlatformException,
    ValidationError,
    DatabaseError,
    ConnectionError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ServiceUnavailableError,
    RateLimitError,
    ConfigurationError
)


logger = get_logger(__name__)


def register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers for the Flask application.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> Tuple[Response, int]:
        """Handle validation errors."""
        logger.warning(
            f"Validation error: {error.message}",
            extra={"extra_fields": error.details}
        )
        return jsonify(error.to_dict()), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error: NotFoundError) -> Tuple[Response, int]:
        """Handle not found errors."""
        logger.info(
            f"Resource not found: {error.message}",
            extra={"extra_fields": error.details}
        )
        return jsonify(error.to_dict()), 404

    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error: AuthenticationError) -> Tuple[Response, int]:
        """Handle authentication errors."""
        logger.warning(
            f"Authentication error: {error.message}",
            extra={"extra_fields": error.details}
        )
        return jsonify(error.to_dict()), 401

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error: AuthorizationError) -> Tuple[Response, int]:
        """Handle authorization errors."""
        logger.warning(
            f"Authorization error: {error.message}",
            extra={"extra_fields": error.details}
        )
        return jsonify(error.to_dict()), 403

    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(error: RateLimitError) -> Tuple[Response, int]:
        """Handle rate limit errors."""
        logger.warning(
            f"Rate limit exceeded: {error.message}",
            extra={"extra_fields": error.details}
        )
        response = jsonify(error.to_dict())
        if "retry_after" in error.details:
            response.headers["Retry-After"] = str(error.details["retry_after"])
        return response, 429

    @app.errorhandler(DatabaseError)
    def handle_database_error(error: DatabaseError) -> Tuple[Response, int]:
        """Handle database errors."""
        logger.error(
            f"Database error: {error.message}",
            extra={"extra_fields": error.details}
        )
        # Don't expose internal database details in production
        return jsonify({
            "error": "DatabaseError",
            "message": "A database error occurred",
            "error_code": error.error_code
        }), 500

    @app.errorhandler(ConnectionError)
    def handle_connection_error(error: ConnectionError) -> Tuple[Response, int]:
        """Handle connection errors."""
        logger.error(
            f"Connection error: {error.message}",
            extra={"extra_fields": error.details}
        )
        return jsonify({
            "error": "ConnectionError",
            "message": "Service connection error",
            "error_code": error.error_code
        }), 503

    @app.errorhandler(ServiceUnavailableError)
    def handle_service_unavailable_error(
        error: ServiceUnavailableError
    ) -> Tuple[Response, int]:
        """Handle service unavailable errors."""
        logger.error(
            f"Service unavailable: {error.message}",
            extra={"extra_fields": error.details}
        )
        return jsonify(error.to_dict()), 503

    @app.errorhandler(ConfigurationError)
    def handle_configuration_error(error: ConfigurationError) -> Tuple[Response, int]:
        """Handle configuration errors."""
        logger.critical(
            f"Configuration error: {error.message}",
            extra={"extra_fields": error.details}
        )
        return jsonify({
            "error": "ConfigurationError",
            "message": "Server configuration error",
            "error_code": error.error_code
        }), 500

    @app.errorhandler(PlatformException)
    def handle_platform_exception(error: PlatformException) -> Tuple[Response, int]:
        """Handle generic platform exceptions."""
        logger.error(
            f"Platform error: {error.message}",
            extra={"extra_fields": error.details}
        )
        return jsonify(error.to_dict()), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException) -> Tuple[Response, int]:
        """Handle Werkzeug HTTP exceptions."""
        logger.warning(
            f"HTTP error: {error.description}",
            extra={"extra_fields": {"code": error.code}}
        )
        return jsonify({
            "error": error.name,
            "message": error.description,
            "status_code": error.code
        }), error.code

    @app.errorhandler(404)
    def handle_404(error) -> Tuple[Response, int]:
        """Handle 404 Not Found errors."""
        logger.info(
            "Route not found",
            extra={"extra_fields": {"path": str(error)}}
        )
        return jsonify({
            "error": "NotFound",
            "message": "The requested resource was not found",
            "status_code": 404
        }), 404

    @app.errorhandler(405)
    def handle_405(error) -> Tuple[Response, int]:
        """Handle 405 Method Not Allowed errors."""
        logger.warning(
            "Method not allowed",
            extra={"extra_fields": {"error": str(error)}}
        )
        return jsonify({
            "error": "MethodNotAllowed",
            "message": "The method is not allowed for the requested URL",
            "status_code": 405
        }), 405

    @app.errorhandler(500)
    def handle_500(error) -> Tuple[Response, int]:
        """Handle 500 Internal Server Error."""
        logger.error(
            "Internal server error",
            exc_info=error
        )
        return jsonify({
            "error": "InternalServerError",
            "message": "An internal server error occurred",
            "status_code": 500
        }), 500

    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception) -> Tuple[Response, int]:
        """Handle unexpected exceptions."""
        logger.critical(
            "Unhandled exception",
            exc_info=error
        )
        return jsonify({
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "status_code": 500
        }), 500


def add_cors_headers(response: Response) -> Response:
    """
    Add CORS headers to response.

    Args:
        response: Flask response object

    Returns:
        Response with CORS headers
    """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response


def add_security_headers(response: Response) -> Response:
    """
    Add security headers to response.

    Args:
        response: Flask response object

    Returns:
        Response with security headers
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def register_response_handlers(app: Flask) -> None:
    """
    Register response handlers for adding common headers.

    Args:
        app: Flask application instance
    """

    @app.after_request
    def after_request(response: Response) -> Response:
        """Add headers to all responses."""
        response = add_cors_headers(response)
        response = add_security_headers(response)
        return response

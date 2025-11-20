"""
API module for the Alkhorayef ESP IoT Platform.

This module provides REST API endpoints and middleware.
"""

from .routes import health_bp, telemetry_bp, diagnostics_bp, docs_bp
from .middleware import (
    register_error_handlers,
    register_response_handlers
)

__all__ = [
    "health_bp",
    "telemetry_bp",
    "diagnostics_bp",
    "docs_bp",
    "register_error_handlers",
    "register_response_handlers",
]

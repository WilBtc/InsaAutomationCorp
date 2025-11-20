"""
Middleware module for the Alkhorayef ESP IoT Platform.

This module provides Flask middleware for error handling and request/response processing.
"""

from .error_handler import (
    register_error_handlers,
    register_response_handlers,
    add_cors_headers,
    add_security_headers
)

__all__ = [
    "register_error_handlers",
    "register_response_handlers",
    "add_cors_headers",
    "add_security_headers",
]

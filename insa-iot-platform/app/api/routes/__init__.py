"""
API routes module for the Alkhorayef ESP IoT Platform.

This module provides REST API endpoints.
"""

from .health import health_bp
from .telemetry import telemetry_bp
from .diagnostics import diagnostics_bp

__all__ = [
    "health_bp",
    "telemetry_bp",
    "diagnostics_bp",
]

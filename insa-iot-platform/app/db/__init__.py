"""
Database module for the Alkhorayef ESP IoT Platform.

This module provides database connection pooling and data models.
"""

from .connection import (
    DatabasePool,
    get_db_pool,
    close_db_pool
)

from .models import (
    DiagnosisType,
    Severity,
    ESPTelemetry,
    DiagnosticResult,
    WellSummary,
    TelemetryBatch,
    SQL_CREATE_TABLES,
    SQL_QUERIES
)

__all__ = [
    # Connection management
    "DatabasePool",
    "get_db_pool",
    "close_db_pool",
    # Models
    "DiagnosisType",
    "Severity",
    "ESPTelemetry",
    "DiagnosticResult",
    "WellSummary",
    "TelemetryBatch",
    "SQL_CREATE_TABLES",
    "SQL_QUERIES",
]

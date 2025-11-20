"""
Core module for the Alkhorayef ESP IoT Platform.

This module provides core functionality including configuration,
logging, and exception handling.
"""

from .config import (
    Config,
    DatabaseConfig,
    RedisConfig,
    LoggingConfig,
    SecurityConfig,
    TelemetryConfig,
    get_config,
    reset_config
)

from .logging import (
    JsonFormatter,
    TextFormatter,
    ContextLogger,
    setup_logging,
    get_logger,
    log_exception,
    log_performance,
    log_audit
)

from .exceptions import (
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

__all__ = [
    # Configuration
    "Config",
    "DatabaseConfig",
    "RedisConfig",
    "LoggingConfig",
    "SecurityConfig",
    "TelemetryConfig",
    "get_config",
    "reset_config",
    # Logging
    "JsonFormatter",
    "TextFormatter",
    "ContextLogger",
    "setup_logging",
    "get_logger",
    "log_exception",
    "log_performance",
    "log_audit",
    # Exceptions
    "PlatformException",
    "ValidationError",
    "DatabaseError",
    "ConnectionError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ServiceUnavailableError",
    "RateLimitError",
    "ConfigurationError",
]

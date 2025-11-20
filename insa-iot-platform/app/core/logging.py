"""
Structured logging setup for the Alkhorayef ESP IoT Platform.

This module provides JSON-formatted structured logging with proper
log rotation and contextual information for production environments.
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import get_config


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def __init__(
        self,
        include_trace: bool = True,
        environment: Optional[str] = None
    ) -> None:
        """
        Initialize JSON formatter.

        Args:
            include_trace: Include stack traces in error logs
            environment: Environment name (development, production, etc.)
        """
        super().__init__()
        self.include_trace = include_trace
        self.environment = environment or "unknown"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": self.environment,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info and self.include_trace:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields from the record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add custom attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "extra_fields", "getMessage"
            ]:
                try:
                    # Only add JSON-serializable values
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Custom text formatter for human-readable logging."""

    def __init__(self) -> None:
        """Initialize text formatter."""
        super().__init__(
            fmt="%(asctime)s [%(levelname)8s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter that adds contextual information to logs."""

    def __init__(
        self,
        logger: logging.Logger,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize context logger.

        Args:
            logger: Base logger instance
            extra: Additional context to include in all logs
        """
        super().__init__(logger, extra or {})

    def process(
        self,
        msg: str,
        kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Process log message and add context.

        Args:
            msg: Log message
            kwargs: Logging keyword arguments

        Returns:
            Processed message and kwargs
        """
        # Add extra context to each log record
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        kwargs["extra"]["extra_fields"] = {
            **self.extra,
            **kwargs["extra"]
        }

        return msg, kwargs


def setup_logging(
    logger_name: Optional[str] = None,
    config: Optional[Any] = None
) -> logging.Logger:
    """
    Set up structured logging with proper handlers.

    Args:
        logger_name: Name for the logger (defaults to root logger)
        config: Configuration object (uses global config if not provided)

    Returns:
        Configured logger instance
    """
    if config is None:
        config = get_config()

    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, config.logging.level))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Choose formatter based on configuration
    if config.logging.format == "json":
        formatter = JsonFormatter(
            include_trace=not config.is_production,
            environment=config.environment
        )
    else:
        formatter = TextFormatter()

    # Console handler (stdout)
    if config.logging.enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.logging.level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    log_file = config.logging.log_dir / f"{logger_name or 'app'}.log"
    max_bytes = config.logging.max_file_size_mb * 1024 * 1024
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=config.logging.backup_count
    )
    file_handler.setLevel(getattr(logging, config.logging.level))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error file handler (only errors and above)
    error_log_file = config.logging.log_dir / f"{logger_name or 'app'}_errors.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=config.logging.backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


def get_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None
) -> ContextLogger:
    """
    Get a context-aware logger instance.

    Args:
        name: Logger name (typically __name__)
        context: Additional context to include in all logs

    Returns:
        Context logger instance
    """
    base_logger = setup_logging(name)
    return ContextLogger(base_logger, context)


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An error occurred",
    **context: Any
) -> None:
    """
    Log an exception with full context.

    Args:
        logger: Logger instance
        exception: Exception to log
        message: Custom error message
        **context: Additional context fields
    """
    logger.error(
        message,
        exc_info=exception,
        extra={"extra_fields": context}
    )


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    **context: Any
) -> None:
    """
    Log performance metrics.

    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        **context: Additional context fields
    """
    logger.info(
        f"Performance: {operation}",
        extra={
            "extra_fields": {
                "operation": operation,
                "duration_ms": duration_ms,
                "metric_type": "performance",
                **context
            }
        }
    )


def log_audit(
    logger: logging.Logger,
    action: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    **context: Any
) -> None:
    """
    Log audit trail events.

    Args:
        logger: Logger instance
        action: Action performed (e.g., 'CREATE', 'UPDATE', 'DELETE')
        user_id: User who performed the action
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        **context: Additional context fields
    """
    logger.info(
        f"Audit: {action}",
        extra={
            "extra_fields": {
                "audit_action": action,
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "metric_type": "audit",
                **context
            }
        }
    )

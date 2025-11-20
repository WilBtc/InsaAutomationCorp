"""
Custom exception classes for the Alkhorayef ESP IoT Platform.

This module defines application-specific exceptions for better error handling
and debugging throughout the platform.
"""

from typing import Optional, Dict, Any


class PlatformException(Exception):
    """Base exception class for all platform-specific exceptions."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize platform exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class ValidationError(PlatformException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field name that failed validation
            **kwargs: Additional error details
        """
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            **kwargs
        )


class DatabaseError(PlatformException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize database error.

        Args:
            message: Error message
            operation: Database operation that failed (e.g., 'INSERT', 'SELECT')
            **kwargs: Additional error details
        """
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            **kwargs
        )


class ConnectionError(PlatformException):
    """Raised when external service connections fail."""

    def __init__(
        self,
        message: str = "Connection failed",
        service: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize connection error.

        Args:
            message: Error message
            service: Service name that failed to connect
            **kwargs: Additional error details
        """
        details = kwargs.pop("details", {})
        if service:
            details["service"] = service
        super().__init__(
            message=message,
            error_code="CONNECTION_ERROR",
            details=details,
            **kwargs
        )


class NotFoundError(PlatformException):
    """Raised when requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize not found error.

        Args:
            message: Error message
            resource_type: Type of resource (e.g., 'well', 'telemetry')
            resource_id: ID of the missing resource
            **kwargs: Additional error details
        """
        details = kwargs.pop("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details=details,
            **kwargs
        )


class AuthenticationError(PlatformException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs
    ) -> None:
        """
        Initialize authentication error.

        Args:
            message: Error message
            **kwargs: Additional error details
        """
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            **kwargs
        )


class AuthorizationError(PlatformException):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize authorization error.

        Args:
            message: Error message
            required_permission: Permission that was required
            **kwargs: Additional error details
        """
        details = kwargs.pop("details", {})
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            **kwargs
        )


class ServiceUnavailableError(PlatformException):
    """Raised when a required service is unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize service unavailable error.

        Args:
            message: Error message
            service: Name of unavailable service
            **kwargs: Additional error details
        """
        details = kwargs.pop("details", {})
        if service:
            details["service"] = service
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
            **kwargs
        )


class RateLimitError(PlatformException):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ) -> None:
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds until retry is allowed
            **kwargs: Additional error details
        """
        details = kwargs.pop("details", {})
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            **kwargs
        )


class ConfigurationError(PlatformException):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize configuration error.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
            **kwargs: Additional error details
        """
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            **kwargs
        )

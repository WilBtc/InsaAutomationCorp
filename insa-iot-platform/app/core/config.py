"""
Configuration management for the Alkhorayef ESP IoT Platform.

This module provides centralized configuration management with environment
variable support and validation.
"""

import os
from typing import Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

from .exceptions import ConfigurationError

# Load environment variables from .env file
load_dotenv()


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""

    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "esp_telemetry"))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "alkhorayef"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    min_pool_size: int = field(default_factory=lambda: int(os.getenv("DB_MIN_POOL_SIZE", "10")))
    max_pool_size: int = field(default_factory=lambda: int(os.getenv("DB_MAX_POOL_SIZE", "20")))
    command_timeout: int = field(default_factory=lambda: int(os.getenv("DB_COMMAND_TIMEOUT", "30")))

    def __post_init__(self) -> None:
        """Validate database configuration."""
        if not self.password:
            raise ConfigurationError(
                message="Database password is required",
                config_key="POSTGRES_PASSWORD"
            )
        if self.port < 1 or self.port > 65535:
            raise ConfigurationError(
                message=f"Invalid database port: {self.port}",
                config_key="POSTGRES_PORT"
            )

    @property
    def connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )


@dataclass
class RedisConfig:
    """Redis cache configuration."""

    host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    password: str = field(default_factory=lambda: os.getenv("REDIS_PASSWORD", ""))
    db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    max_connections: int = field(default_factory=lambda: int(os.getenv("REDIS_MAX_CONNECTIONS", "50")))
    socket_timeout: int = field(default_factory=lambda: int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")))
    socket_connect_timeout: int = field(default_factory=lambda: int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")))

    def __post_init__(self) -> None:
        """Validate Redis configuration."""
        if self.port < 1 or self.port > 65535:
            raise ConfigurationError(
                message=f"Invalid Redis port: {self.port}",
                config_key="REDIS_PORT"
            )

    @property
    def connection_string(self) -> str:
        """Build Redis connection string."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = field(default_factory=lambda: os.getenv("LOG_FORMAT", "json"))
    log_dir: Path = field(default_factory=lambda: Path(os.getenv("LOG_DIR", "logs")))
    max_file_size_mb: int = field(default_factory=lambda: int(os.getenv("LOG_MAX_FILE_SIZE_MB", "100")))
    backup_count: int = field(default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "10")))
    enable_console: bool = field(default_factory=lambda: os.getenv("LOG_CONSOLE", "true").lower() == "true")

    def __post_init__(self) -> None:
        """Validate and normalize logging configuration."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.level = self.level.upper()
        if self.level not in valid_levels:
            raise ConfigurationError(
                message=f"Invalid log level: {self.level}. Must be one of {valid_levels}",
                config_key="LOG_LEVEL"
            )

        valid_formats = ["json", "text"]
        if self.format not in valid_formats:
            raise ConfigurationError(
                message=f"Invalid log format: {self.format}. Must be one of {valid_formats}",
                config_key="LOG_FORMAT"
            )

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    # Enable/disable rate limiting
    enabled: bool = field(default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true")

    # Default limits per role (requests per minute)
    admin_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_ADMIN_PER_MINUTE", "1000")))
    admin_per_hour: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_ADMIN_PER_HOUR", "50000")))
    admin_per_day: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_ADMIN_PER_DAY", "1000000")))

    operator_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_OPERATOR_PER_MINUTE", "500")))
    operator_per_hour: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_OPERATOR_PER_HOUR", "25000")))
    operator_per_day: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_OPERATOR_PER_DAY", "500000")))

    viewer_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_VIEWER_PER_MINUTE", "100")))
    viewer_per_hour: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_VIEWER_PER_HOUR", "5000")))
    viewer_per_day: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_VIEWER_PER_DAY", "100000")))

    anonymous_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_ANONYMOUS_PER_MINUTE", "10")))
    anonymous_per_hour: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_ANONYMOUS_PER_HOUR", "100")))
    anonymous_per_day: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_ANONYMOUS_PER_DAY", "1000")))

    # Global rate limit (across all users)
    global_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_GLOBAL_PER_MINUTE", "10000")))

    # Burst handling
    burst_multiplier: float = field(default_factory=lambda: float(os.getenv("RATE_LIMIT_BURST_MULTIPLIER", "2.0")))
    burst_duration_seconds: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_BURST_DURATION", "10")))

    # Whitelisted IPs (comma-separated)
    whitelisted_ips: List[str] = field(
        default_factory=lambda: [ip.strip() for ip in os.getenv("RATE_LIMIT_WHITELIST_IPS", "").split(",") if ip.strip()]
    )

    # Endpoint-specific overrides
    telemetry_batch_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_TELEMETRY_BATCH_PER_MINUTE", "50")))
    ml_train_per_hour: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_ML_TRAIN_PER_HOUR", "10")))

    def __post_init__(self) -> None:
        """Validate rate limit configuration."""
        # Validate burst multiplier
        if self.burst_multiplier < 1.0:
            raise ConfigurationError(
                message="Burst multiplier must be >= 1.0",
                config_key="RATE_LIMIT_BURST_MULTIPLIER"
            )

        # Validate limits are positive
        limits = [
            self.admin_per_minute, self.admin_per_hour, self.admin_per_day,
            self.operator_per_minute, self.operator_per_hour, self.operator_per_day,
            self.viewer_per_minute, self.viewer_per_hour, self.viewer_per_day,
            self.anonymous_per_minute, self.anonymous_per_hour, self.anonymous_per_day,
            self.global_per_minute
        ]

        if any(limit < 1 for limit in limits):
            raise ConfigurationError(
                message="All rate limits must be positive integers",
                config_key="RATE_LIMIT_*"
            )


@dataclass
class SecurityConfig:
    """Security configuration."""

    # JWT Configuration
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", ""))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_access_token_expire_minutes: int = field(
        default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    )
    jwt_refresh_token_expire_days: int = field(
        default_factory=lambda: int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    )

    # Legacy SECRET_KEY support (fallback to JWT_SECRET_KEY)
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", os.getenv("JWT_SECRET_KEY", "")))

    # Access token expiration (legacy, use jwt_access_token_expire_minutes)
    access_token_expire_minutes: int = field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",
                                               os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
    )

    # CORS Configuration
    allowed_origins: List[str] = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(",")
    )

    # Legacy rate limiting (deprecated - use RateLimitConfig)
    rate_limit_requests: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    )
    rate_limit_window_seconds: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    )

    def __post_init__(self) -> None:
        """Validate security configuration."""
        # Use JWT_SECRET_KEY as primary, SECRET_KEY as fallback
        if not self.jwt_secret_key and not self.secret_key:
            raise ConfigurationError(
                message="JWT_SECRET_KEY is required for production use",
                config_key="JWT_SECRET_KEY"
            )

        # Ensure jwt_secret_key is set
        if not self.jwt_secret_key:
            self.jwt_secret_key = self.secret_key

        if len(self.jwt_secret_key) < 32:
            raise ConfigurationError(
                message="JWT_SECRET_KEY must be at least 32 characters long",
                config_key="JWT_SECRET_KEY"
            )


@dataclass
class TelemetryConfig:
    """Telemetry data configuration."""

    retention_days: int = field(default_factory=lambda: int(os.getenv("TELEMETRY_RETENTION_DAYS", "30")))
    batch_size: int = field(default_factory=lambda: int(os.getenv("TELEMETRY_BATCH_SIZE", "1000")))
    ingestion_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("TELEMETRY_INGESTION_TIMEOUT", "10"))
    )
    cache_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("TELEMETRY_CACHE_TTL", "300")))

    def __post_init__(self) -> None:
        """Validate telemetry configuration."""
        if self.retention_days < 1:
            raise ConfigurationError(
                message="Telemetry retention must be at least 1 day",
                config_key="TELEMETRY_RETENTION_DAYS"
            )
        if self.batch_size < 1 or self.batch_size > 10000:
            raise ConfigurationError(
                message="Batch size must be between 1 and 10000",
                config_key="TELEMETRY_BATCH_SIZE"
            )


@dataclass
class Config:
    """Main application configuration."""

    # Application settings
    app_name: str = "Alkhorayef ESP IoT Platform"
    version: str = "1.0.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)

    def __post_init__(self) -> None:
        """Validate main configuration."""
        valid_environments = ["development", "staging", "production"]
        if self.environment not in valid_environments:
            raise ConfigurationError(
                message=f"Invalid environment: {self.environment}. Must be one of {valid_environments}",
                config_key="ENVIRONMENT"
            )

        if self.port < 1 or self.port > 65535:
            raise ConfigurationError(
                message=f"Invalid port: {self.port}",
                config_key="PORT"
            )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def validate(self) -> None:
        """
        Perform comprehensive configuration validation.

        Raises:
            ConfigurationError: If any configuration is invalid
        """
        # All validation is done in __post_init__ of dataclasses
        if self.is_production and self.debug:
            raise ConfigurationError(
                message="DEBUG mode should not be enabled in production",
                config_key="DEBUG"
            )


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create global configuration instance.

    Returns:
        Config: Application configuration

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _config
    if _config is None:
        _config = Config()
        _config.validate()
    return _config


def reset_config() -> None:
    """Reset global configuration (mainly for testing)."""
    global _config
    _config = None

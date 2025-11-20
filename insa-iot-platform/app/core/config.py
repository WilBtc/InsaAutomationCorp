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
class SecurityConfig:
    """Security configuration."""

    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    )
    allowed_origins: List[str] = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(",")
    )
    rate_limit_requests: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    )
    rate_limit_window_seconds: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    )

    def __post_init__(self) -> None:
        """Validate security configuration."""
        if not self.secret_key:
            raise ConfigurationError(
                message="SECRET_KEY is required for production use",
                config_key="SECRET_KEY"
            )
        if len(self.secret_key) < 32:
            raise ConfigurationError(
                message="SECRET_KEY must be at least 32 characters long",
                config_key="SECRET_KEY"
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

"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "INSA CRM System"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # ERPNext (using Docker exec method, not API keys)
    ERPNEXT_API_URL: str
    ERPNEXT_USERNAME: str = "Administrator"
    ERPNEXT_PASSWORD: str = "admin"

    # Qdrant
    QDRANT_HOST: str = "100.107.50.52"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None

    # InvenTree
    INVENTREE_API_URL: str = "http://localhost:8002/api"
    INVENTREE_TOKEN: str | None = None

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://100.100.101.1",
        "http://100.105.64.109"
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    STRUCTLOG_DEV_MODE: bool = False

    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_FROM: str = "crm@insaing.com"

    # Agent Settings
    ENABLE_AGENT_EXECUTION: bool = True
    ENABLE_SECURITY_SCANS: bool = False
    MAX_CONCURRENT_AGENTS: int = 5
    DEFAULT_AGENT_MODEL: str = "claude-sonnet-4-5-20250929"
    FAST_AGENT_MODEL: str = "claude-haiku-20250715"

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    AGENTOPS_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()

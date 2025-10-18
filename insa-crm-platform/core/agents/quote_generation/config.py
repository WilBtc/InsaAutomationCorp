"""
Configuration for Quote Generation Agent
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class QuoteGenerationConfig(BaseSettings):
    """Configuration for quote generation system"""

    # Database
    database_url: str = "postgresql://insa_crm_user:[REDACTED]@localhost:5432/insa_crm"

    # ChromaDB (RAG Knowledge Base)
    chromadb_path: str = "/var/lib/insa-crm/quote_knowledge_base"
    chromadb_collection: str = "insa_projects"

    # ERPNext Integration
    erpnext_api_url: str = "http://100.100.101.1:9000/api"
    erpnext_username: str = "Administrator"
    erpnext_password: str = "admin"
    erpnext_docker_container: str = "frappe_docker_backend_1"

    # InvenTree Integration
    inventree_api_url: str = "http://100.100.101.1:9600/api"
    inventree_token: str = os.getenv("INVENTREE_API_TOKEN", "")

    # Mautic Integration
    mautic_api_url: str = "http://100.100.101.1:9700/api"
    mautic_username: str = "admin"
    mautic_password: str = "mautic_admin_2025"

    # Claude Code (Local AI - Zero API Cost)
    claude_timeout: int = 120  # seconds
    claude_max_retries: int = 3

    # Quote Generation Settings
    default_markup_percentage: float = 30.0  # 30% margin
    labor_rate_per_hour: float = 85.0  # USD per hour
    engineering_rate_per_hour: float = 120.0  # USD per hour

    # Confidence Thresholds
    min_confidence_auto_approve: float = 0.85  # Auto-send if >85% confidence
    min_confidence_send: float = 0.70  # Send with human review if >70%

    # Email Settings
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_from: str = "quotes@insaing.com"

    # File Storage
    quotes_storage_path: str = "/var/lib/insa-crm/quotes"
    templates_path: str = "/home/wil/insa-crm-platform/core/agents/quote_generation/templates"

    # Project Reference Data
    reference_projects_path: str = "/home/wil/insa-crm-platform/projects/customers"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = "/home/wil/insa-crm-platform/core/.env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


# Global config instance
config = QuoteGenerationConfig()

"""
SQLAlchemy ORM Models
=====================
Database models for user settings, sessions, exports, and notifications
Compatible with both PostgreSQL and SQLite
"""

from datetime import datetime, time
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Boolean, Integer, BigInteger, Text,
    DateTime, Date, Time, JSON, Enum as SAEnum, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, INET, ARRAY
from sqlalchemy.sql import func
import enum

from ..database import Base

# ====================================
# ENUMS
# ====================================

class ThemeType(str, enum.Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class DashboardType(str, enum.Enum):
    STANDARD = "standard"
    MODERN = "modern"
    DARK = "dark"
    GLASS = "glass"


class LanguageType(str, enum.Enum):
    EN = "en"
    FR = "fr"
    DE = "de"
    ES = "es"


class DateFormatType(str, enum.Enum):
    MM_DD_YYYY = "MM/DD/YYYY"
    DD_MM_YYYY = "DD/MM/YYYY"
    YYYY_MM_DD = "YYYY-MM-DD"


class ExportDataType(str, enum.Enum):
    DEVICES = "devices"
    TELEMETRY = "telemetry"
    ALERTS = "alerts"
    ALL = "all"


class ExportFormat(str, enum.Enum):
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


class ExportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class EmailDigestType(str, enum.Enum):
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class SeverityType(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ====================================
# HELPER FUNCTIONS FOR CROSS-DB COMPATIBILITY
# ====================================

def UUID_Column(primary_key=False, default=None):
    """
    Create a UUID column that works with both PostgreSQL and SQLite
    """
    if default is None and not primary_key:
        return Column(String(36))
    else:
        return Column(
            String(36),
            primary_key=primary_key,
            default=lambda: str(uuid4()) if default is None else default
        )


# ====================================
# 1. USER PREFERENCES MODEL
# ====================================

class UserPreference(Base):
    __tablename__ = "user_preferences"

    # Primary Key
    preference_id = UUID_Column(primary_key=True)
    user_id = Column(String(36), nullable=False)
    tenant_id = Column(String(36), nullable=False)

    # Appearance Settings
    theme = Column(String(20), default="dark")
    primary_color = Column(String(7), default="#0ea5e9")
    compact_mode = Column(Boolean, default=False)

    # Dashboard Settings
    auto_refresh = Column(Boolean, default=True)
    refresh_interval = Column(Integer, default=30)
    default_dashboard = Column(String(50), default="standard")

    # Language & Region
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="DD/MM/YYYY")

    # Device Settings
    device_auto_discovery = Column(Boolean, default=True)
    device_auto_provision = Column(Boolean, default=False)
    device_heartbeat_interval = Column(Integer, default=60)
    device_offline_threshold = Column(Integer, default=300)

    # Alert Settings
    alert_aggregation = Column(Boolean, default=True)
    alert_auto_acknowledge = Column(Boolean, default=False)
    alert_retention_days = Column(Integer, default=30)

    # Data & Privacy
    analytics_enabled = Column(Boolean, default=True)
    crash_reports_enabled = Column(Boolean, default=True)
    telemetry_retention_days = Column(Integer, default=90)

    # Advanced Settings
    debug_mode = Column(Boolean, default=False)
    experimental_features = Column(Boolean, default=False)
    hardware_acceleration = Column(Boolean, default=True)
    animation_effects = Column(Boolean, default=True)

    # Session Settings
    session_timeout_minutes = Column(Integer, default=60)

    # Additional settings
    advanced_settings = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant_preferences'),
        Index('idx_user_preferences_user', 'user_id'),
        Index('idx_user_preferences_tenant', 'tenant_id'),
    )


# ====================================
# 2. USER SESSIONS MODEL
# ====================================

class UserSession(Base):
    __tablename__ = "user_sessions"

    # Primary Key
    session_id = UUID_Column(primary_key=True)
    user_id = Column(String(36), nullable=False)
    tenant_id = Column(String(36), nullable=False)

    # Session metadata
    ip_address = Column(String(45))  # Supports IPv4 and IPv6
    user_agent = Column(Text)
    device_type = Column(String(50))
    browser = Column(String(100))
    os = Column(String(100))
    location_country = Column(String(2))
    location_city = Column(String(100))

    # Session state
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    terminated_at = Column(DateTime)
    termination_reason = Column(String(100))

    # Security
    token_hash = Column(String(255))
    refresh_token_hash = Column(String(255))

    # Metadata
    metadata = Column(JSON, default=dict)

    __table_args__ = (
        Index('idx_user_sessions_user', 'user_id'),
        Index('idx_user_sessions_tenant', 'tenant_id'),
        Index('idx_user_sessions_active', 'is_active'),
        Index('idx_user_sessions_expires', 'expires_at'),
        Index('idx_user_sessions_last_activity', 'last_activity'),
    )


# ====================================
# 3. DATA EXPORTS MODEL
# ====================================

class DataExport(Base):
    __tablename__ = "data_exports"

    # Primary Key
    export_id = UUID_Column(primary_key=True)
    user_id = Column(String(36), nullable=False)
    tenant_id = Column(String(36), nullable=False)

    # Export configuration
    data_type = Column(String(50), nullable=False)
    format = Column(String(20), nullable=False)
    filters = Column(JSON, default=dict)

    # Export status
    status = Column(String(20), default="pending")
    progress_percent = Column(Integer, default=0)

    # Export results
    file_size = Column(BigInteger)
    file_location = Column(Text)
    file_url = Column(Text)
    record_count = Column(BigInteger)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)

    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)

    # Metadata
    metadata = Column(JSON, default=dict)

    __table_args__ = (
        Index('idx_data_exports_user', 'user_id'),
        Index('idx_data_exports_tenant', 'tenant_id'),
        Index('idx_data_exports_status', 'status'),
        Index('idx_data_exports_expires', 'expires_at'),
    )


# ====================================
# 4. NOTIFICATION PREFERENCES MODEL
# ====================================

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    # Primary Key
    pref_id = UUID_Column(primary_key=True)
    user_id = Column(String(36), nullable=False)
    tenant_id = Column(String(36), nullable=False)

    # Email Notifications
    email_enabled = Column(Boolean, default=True)
    email_address = Column(String(255))
    email_digest = Column(String(20), default="immediate")
    email_critical_alerts = Column(Boolean, default=True)
    email_device_offline = Column(Boolean, default=True)
    email_daily_summary = Column(Boolean, default=False)
    email_weekly_reports = Column(Boolean, default=True)

    # Push Notifications
    push_enabled = Column(Boolean, default=True)
    push_sound_enabled = Column(Boolean, default=False)

    # SMS Notifications
    sms_enabled = Column(Boolean, default=False)
    phone_number = Column(String(50))
    sms_critical_only = Column(Boolean, default=True)

    # In-App Notifications
    in_app_enabled = Column(Boolean, default=True)

    # Webhook Notifications
    webhook_enabled = Column(Boolean, default=False)
    webhook_url = Column(Text)
    webhook_events = Column(JSON, default=lambda: ["alert.critical", "device.offline"])
    webhook_secret = Column(String(255))

    # Alert Filtering
    min_severity = Column(String(20), default="warning")

    # Quiet Hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(Time)
    quiet_hours_end = Column(Time)
    quiet_hours_timezone = Column(String(50), default="UTC")
    quiet_hours_days = Column(JSON, default=lambda: [1, 2, 3, 4, 5])

    # Advanced settings
    advanced_settings = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant_notification_prefs'),
        Index('idx_notification_preferences_user', 'user_id'),
        Index('idx_notification_preferences_tenant', 'tenant_id'),
        Index('idx_notification_preferences_email', 'email_address'),
    )


# ====================================
# 5. API KEYS MODEL
# ====================================

class APIKey(Base):
    __tablename__ = "api_keys"

    # Primary Key
    key_id = UUID_Column(primary_key=True)
    user_id = Column(String(36), nullable=False)
    tenant_id = Column(String(36), nullable=False)

    # Key details
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    key_prefix = Column(String(20))

    # Permissions
    permissions = Column(JSON, default=list)
    rate_limit = Column(Integer, default=1000)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)
    revoke_reason = Column(Text)

    # Metadata
    metadata = Column(JSON, default=dict)

    __table_args__ = (
        Index('idx_api_keys_user', 'user_id'),
        Index('idx_api_keys_tenant', 'tenant_id'),
        Index('idx_api_keys_hash', 'key_hash'),
        Index('idx_api_keys_active', 'is_active'),
    )


# ====================================
# 6. USER ACTIVITY LOG MODEL
# ====================================

class UserActivityLog(Base):
    __tablename__ = "user_activity_log"

    # Primary Key
    activity_id = UUID_Column(primary_key=True)
    user_id = Column(String(36), nullable=False)
    tenant_id = Column(String(36), nullable=False)
    session_id = Column(String(36))

    # Activity details
    activity_type = Column(String(50), nullable=False)
    activity_category = Column(String(50))
    activity_description = Column(Text)
    resource_type = Column(String(50))
    resource_id = Column(String(36))

    # Request details
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_path = Column(Text)

    # Response details
    status_code = Column(Integer)
    response_time_ms = Column(Integer)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow)
    changes = Column(JSON)
    metadata = Column(JSON, default=dict)

    __table_args__ = (
        Index('idx_activity_log_user', 'user_id'),
        Index('idx_activity_log_tenant', 'tenant_id'),
        Index('idx_activity_log_session', 'session_id'),
        Index('idx_activity_log_type', 'activity_type'),
        Index('idx_activity_log_created', 'created_at'),
    )

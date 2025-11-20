#!/usr/bin/env python3
"""
Alkhorayef ESP IoT Platform - Configuration Validator
Validates environment configuration before deployment
"""

import os
import sys
from typing import List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_header(text: str) -> None:
    """Print section header"""
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")


def print_success(text: str) -> None:
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def check_required_vars() -> Tuple[bool, List[str]]:
    """Check all required environment variables are set"""
    print_header("1. Required Environment Variables")

    required_vars = [
        # Application
        'ENVIRONMENT',
        'LOG_LEVEL',

        # Database
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'DATABASE_URL',

        # Redis
        'REDIS_HOST',
        'REDIS_PORT',
        'REDIS_PASSWORD',
        'REDIS_URL',

        # Security
        'JWT_SECRET_KEY',
        'JWT_ALGORITHM',

        # API
        'API_PORT',
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var}: {value[:20]}..." if len(str(value)) > 20 else f"{var}: {value}")
        else:
            print_error(f"{var}: NOT SET")
            missing.append(var)

    if missing:
        print_error(f"\nMissing {len(missing)} required variable(s)")
        return False, missing
    else:
        print_success(f"\nAll {len(required_vars)} required variables are set")
        return True, []


def check_security() -> bool:
    """Check security configuration"""
    print_header("2. Security Configuration")

    issues = []

    # Check JWT secret
    jwt_secret = os.getenv('JWT_SECRET_KEY', '')
    if 'CHANGE_ME' in jwt_secret:
        print_error("JWT_SECRET_KEY contains 'CHANGE_ME' placeholder")
        issues.append('jwt_secret')
    elif len(jwt_secret) < 32:
        print_warning(f"JWT_SECRET_KEY is short ({len(jwt_secret)} chars, recommended 32+)")
        issues.append('jwt_secret_weak')
    else:
        print_success(f"JWT_SECRET_KEY: Strong ({len(jwt_secret)} chars)")

    # Check database password
    db_password = os.getenv('POSTGRES_PASSWORD', '')
    if 'CHANGE_ME' in db_password:
        print_error("POSTGRES_PASSWORD contains 'CHANGE_ME' placeholder")
        issues.append('db_password')
    elif len(db_password) < 16:
        print_warning(f"POSTGRES_PASSWORD is weak ({len(db_password)} chars)")
        issues.append('db_password_weak')
    else:
        print_success(f"POSTGRES_PASSWORD: Strong ({len(db_password)} chars)")

    # Check Redis password
    redis_password = os.getenv('REDIS_PASSWORD', '')
    if 'CHANGE_ME' in redis_password:
        print_error("REDIS_PASSWORD contains 'CHANGE_ME' placeholder")
        issues.append('redis_password')
    elif len(redis_password) < 16:
        print_warning(f"REDIS_PASSWORD is weak ({len(redis_password)} chars)")
        issues.append('redis_password_weak')
    else:
        print_success(f"REDIS_PASSWORD: Strong ({len(redis_password)} chars)")

    # Check DEBUG_MODE
    debug_mode = os.getenv('DEBUG_MODE', 'false').lower()
    environment = os.getenv('ENVIRONMENT', 'development')
    if debug_mode == 'true' and environment == 'production':
        print_error("DEBUG_MODE=true in production environment!")
        issues.append('debug_in_production')
    else:
        print_success(f"DEBUG_MODE: {debug_mode} (environment: {environment})")

    # Check CORS
    cors_origins = os.getenv('CORS_ORIGINS', '')
    if '*' in cors_origins and environment == 'production':
        print_error("CORS allows wildcard (*) in production!")
        issues.append('cors_wildcard')
    else:
        print_success(f"CORS_ORIGINS: {cors_origins}")

    if issues:
        print_error(f"\n{len(issues)} security issue(s) found")
        return False
    else:
        print_success("\nSecurity configuration OK")
        return True


def check_database_config() -> bool:
    """Check database configuration"""
    print_header("3. Database Configuration")

    issues = []

    # Pool settings
    pool_min = int(os.getenv('DB_POOL_MIN_SIZE', '10'))
    pool_max = int(os.getenv('DB_POOL_MAX_SIZE', '20'))

    if pool_min > pool_max:
        print_error(f"DB_POOL_MIN_SIZE ({pool_min}) > DB_POOL_MAX_SIZE ({pool_max})")
        issues.append('pool_size')
    elif pool_max > 50:
        print_warning(f"DB_POOL_MAX_SIZE is very high ({pool_max})")
    else:
        print_success(f"Pool size: {pool_min} min, {pool_max} max")

    # Connection timeout
    timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    if timeout < 10:
        print_warning(f"DB_POOL_TIMEOUT is very low ({timeout}s)")
    else:
        print_success(f"Connection timeout: {timeout}s")

    # Query timeout
    query_timeout = int(os.getenv('DB_QUERY_TIMEOUT', '30'))
    if query_timeout < 10:
        print_warning(f"DB_QUERY_TIMEOUT is very low ({query_timeout}s)")
    else:
        print_success(f"Query timeout: {query_timeout}s")

    return len(issues) == 0


def check_retention_policies() -> bool:
    """Check data retention configuration"""
    print_header("4. Data Retention Policies")

    issues = []

    telemetry_retention = int(os.getenv('TELEMETRY_RETENTION_DAYS', '30'))
    backup_retention = int(os.getenv('BACKUP_RETENTION_DAYS', '90'))

    # Critical requirement: Azure should only have 30 days
    if telemetry_retention != 30:
        print_warning(f"TELEMETRY_RETENTION_DAYS is {telemetry_retention} (recommended: 30 for Azure)")
    else:
        print_success(f"Telemetry retention: {telemetry_retention} days (Azure backup requirement)")

    # Backup should be longer
    if backup_retention <= telemetry_retention:
        print_error(f"BACKUP_RETENTION_DAYS ({backup_retention}) should be > TELEMETRY_RETENTION_DAYS ({telemetry_retention})")
        issues.append('backup_retention')
    else:
        print_success(f"Backup retention: {backup_retention} days")

    # Check automated backup
    auto_backup = os.getenv('ENABLE_AUTOMATED_BACKUP', 'false').lower()
    if auto_backup != 'true':
        print_warning("ENABLE_AUTOMATED_BACKUP is not enabled")
    else:
        print_success("Automated backups: enabled")
        schedule = os.getenv('BACKUP_SCHEDULE', '')
        print_success(f"Backup schedule: {schedule}")

    return len(issues) == 0


def check_performance() -> bool:
    """Check performance settings"""
    print_header("5. Performance Configuration")

    # Gunicorn workers
    workers = int(os.getenv('GUNICORN_WORKERS', '4'))
    if workers < 2:
        print_warning(f"GUNICORN_WORKERS is low ({workers})")
    elif workers > 16:
        print_warning(f"GUNICORN_WORKERS is very high ({workers})")
    else:
        print_success(f"Gunicorn workers: {workers}")

    # Request timeout
    timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))
    print_success(f"Request timeout: {timeout}s")

    # Redis connections
    redis_max = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
    print_success(f"Redis max connections: {redis_max}")

    # Redis TTL
    redis_ttl = int(os.getenv('REDIS_DEFAULT_TTL', '300'))
    print_success(f"Redis default TTL: {redis_ttl}s")

    return True


def check_monitoring() -> bool:
    """Check monitoring configuration"""
    print_header("6. Monitoring & Alerting")

    # Metrics
    metrics_enabled = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    print_success(f"Metrics: {'enabled' if metrics_enabled else 'disabled'}")

    # Tracing
    tracing_enabled = os.getenv('ENABLE_TRACING', 'false').lower() == 'true'
    print_success(f"Tracing: {'enabled' if tracing_enabled else 'disabled'}")

    # Email alerts
    alert_recipients = os.getenv('ALERT_EMAIL_RECIPIENTS', '')
    if alert_recipients:
        print_success(f"Email alerts: {alert_recipients}")
    else:
        print_warning("ALERT_EMAIL_RECIPIENTS not configured")

    # Slack
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL', '')
    if slack_webhook:
        print_success("Slack webhook: configured")
    else:
        print_warning("SLACK_WEBHOOK_URL not configured")

    return True


def main():
    """Main validation function"""
    print(f"\n{BOLD}{BLUE}Alkhorayef ESP IoT Platform - Configuration Validator{RESET}")
    print(f"{BOLD}Validating environment configuration...{RESET}")

    all_checks = []

    # Run all checks
    all_checks.append(check_required_vars()[0])
    all_checks.append(check_security())
    all_checks.append(check_database_config())
    all_checks.append(check_retention_policies())
    all_checks.append(check_performance())
    all_checks.append(check_monitoring())

    # Final summary
    print_header("Validation Summary")

    if all(all_checks):
        print_success("All validation checks passed!")
        print_success("Configuration is ready for deployment")
        return 0
    else:
        failed = len([c for c in all_checks if not c])
        print_error(f"{failed} validation check(s) failed")
        print_error("Please fix the issues before deployment")
        return 1


if __name__ == '__main__':
    sys.exit(main())

#!/bin/bash
#
# TimescaleDB Restore Script
#
# This script restores a TimescaleDB backup with safety checks.
#
# Usage:
#   ./restore_timescaledb.sh <backup_file> [--force]
#
# Safety features:
# - Requires --force flag to prevent accidental restores
# - Creates safety backup before restore
# - Validates backup file before proceeding
# - Can restore from local or Azure backups

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Database configuration
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5440}"
DB_NAME="${POSTGRES_DB:-esp_telemetry}"
DB_USER="${POSTGRES_USER:-esp_user}"
DB_PASSWORD="${POSTGRES_PASSWORD}"
CONTAINER_NAME="${TIMESCALEDB_CONTAINER:-alkhorayef-timescaledb}"

# ============================================================================
# Functions
# ============================================================================

usage() {
    cat << EOF
Usage: $0 <backup_file> [--force]

Restore a TimescaleDB backup.

Arguments:
  backup_file    Path to backup file (.sql.gz)
  --force        Required flag to confirm restore operation

Examples:
  # Restore from local backup
  $0 /path/to/backup.sql.gz --force

  # Restore latest backup
  $0 \$(ls -t backups/*.sql.gz | head -1) --force

Safety:
  - Creates safety backup before restore
  - Validates backup integrity
  - Requires --force flag
EOF
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    log "ERROR: $*" >&2
    exit 1
}

validate_backup() {
    local backup_file="$1"

    log "Validating backup file..."

    # Check file exists
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
    fi

    # Check file is not empty
    if [ ! -s "$backup_file" ]; then
        error "Backup file is empty"
    fi

    # Check gzip integrity
    if ! gzip -t "$backup_file" 2>/dev/null; then
        error "Backup file is corrupted (failed gzip test)"
    fi

    # Check checksum if available
    if [ -f "${backup_file}.md5" ]; then
        log "Verifying checksum..."
        if md5sum -c "${backup_file}.md5" > /dev/null 2>&1; then
            log "Checksum verification passed"
        else
            error "Checksum verification failed"
        fi
    fi

    log "Backup file validation passed"
}

create_safety_backup() {
    log "Creating safety backup before restore..."

    local safety_backup="$PROJECT_DIR/backups/safety_backup_$(date +%Y%m%d_%H%M%S).sql.gz"

    if docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
        pg_dump -U "$DB_USER" -d "$DB_NAME" --format=plain --no-owner | gzip -6 > "$safety_backup"; then
        log "Safety backup created: $safety_backup"
        echo "$safety_backup" > /tmp/timescaledb_safety_backup_path.txt
    else
        error "Failed to create safety backup"
    fi
}

perform_restore() {
    local backup_file="$1"

    log "Starting restore from: $backup_file"
    log "WARNING: This will replace all data in database '$DB_NAME'"
    log "Sleeping for 5 seconds... Press Ctrl+C to cancel"
    sleep 5

    # Drop and recreate database
    log "Dropping existing database..."
    if ! docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null; then
        error "Failed to drop database"
    fi

    log "Creating fresh database..."
    if ! docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -U "$DB_USER" -d postgres -c "CREATE DATABASE ${DB_NAME};" 2>/dev/null; then
        error "Failed to create database"
    fi

    # Enable TimescaleDB extension
    log "Enabling TimescaleDB extension..."
    if ! docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;" 2>/dev/null; then
        error "Failed to enable TimescaleDB extension"
    fi

    # Restore backup
    log "Restoring backup data..."
    if zcat "$backup_file" | docker exec -i -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
        log "Restore completed successfully"
    else
        error "Restore failed - use safety backup to recover"
    fi
}

verify_restore() {
    log "Verifying restored database..."

    # Check table count
    local table_count=$(docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

    log "Tables restored: $(echo $table_count | tr -d ' ')"

    # Check record count
    local record_count=$(docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM esp_telemetry;" 2>/dev/null || echo "0")

    log "Records in esp_telemetry: $(echo $record_count | tr -d ' ')"

    # Check if hypertables exist
    local hypertable_count=$(docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM timescaledb_information.hypertables;" 2>/dev/null || echo "0")

    log "Hypertables: $(echo $hypertable_count | tr -d ' ')"

    if [ "$(echo $table_count | tr -d ' ')" -gt 0 ]; then
        log "Database restore verification passed"
    else
        error "No tables found after restore"
    fi
}

# ============================================================================
# Main
# ============================================================================

main() {
    # Parse arguments
    if [ $# -lt 2 ]; then
        usage
    fi

    local backup_file="$1"
    local force_flag="${2:-}"

    if [ "$force_flag" != "--force" ]; then
        log "ERROR: --force flag required to prevent accidental restores"
        usage
    fi

    log "==================================================================="
    log "TimescaleDB Restore Started"
    log "==================================================================="

    # Validate backup
    validate_backup "$backup_file"

    # Create safety backup
    create_safety_backup

    # Perform restore
    perform_restore "$backup_file"

    # Verify restore
    verify_restore

    log "==================================================================="
    log "Restore completed successfully"
    log "==================================================================="
    log ""
    log "Safety backup location: $(cat /tmp/timescaledb_safety_backup_path.txt 2>/dev/null || echo 'Unknown')"
}

main "$@"

#!/bin/bash
#
# TimescaleDB Automated Backup Script
#
# This script performs automated backups of the TimescaleDB database with:
# - Local compressed backups (30-day retention)
# - Azure Blob Storage uploads (unlimited retention)
# - Integrity verification
# - Health monitoring
#
# Usage:
#   ./backup_timescaledb.sh [--test]
#
# Environment variables required:
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#   AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_CONTAINER, AZURE_STORAGE_KEY (optional)

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment from .env if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Backup configuration
BACKUP_DIR="${BACKUP_LOCAL_PATH:-/var/backups/timescaledb}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
COMPRESSION_LEVEL="${BACKUP_COMPRESSION_LEVEL:-6}"
MIN_DISK_SPACE_GB=10

# Database configuration
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5440}"
DB_NAME="${POSTGRES_DB:-esp_telemetry}"
DB_USER="${POSTGRES_USER:-esp_user}"
DB_PASSWORD="${POSTGRES_PASSWORD}"

# Container name (if using Docker)
CONTAINER_NAME="${TIMESCALEDB_CONTAINER:-alkhorayef-timescaledb}"

# Azure configuration (optional)
AZURE_ACCOUNT="${AZURE_STORAGE_ACCOUNT:-}"
AZURE_CONTAINER="${AZURE_STORAGE_CONTAINER:-timescaledb-backups}"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="timescaledb_backup_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Logging
LOG_FILE="${BACKUP_DIR}/backup.log"
TEST_MODE=false

# ============================================================================
# Functions
# ============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR" "$*"
    exit 1
}

check_prerequisites() {
    log "INFO" "Checking prerequisites..."

    # Check if running in test mode
    if [ "${1:-}" = "--test" ]; then
        TEST_MODE=true
        log "INFO" "Running in TEST MODE"
    fi

    # Check backup directory
    if [ ! -d "$BACKUP_DIR" ]; then
        log "INFO" "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR" || error "Failed to create backup directory"
    fi

    # Check disk space
    local available_space=$(df -BG "$BACKUP_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt "$MIN_DISK_SPACE_GB" ]; then
        error "Insufficient disk space. Available: ${available_space}GB, Required: ${MIN_DISK_SPACE_GB}GB"
    fi
    log "INFO" "Disk space check passed: ${available_space}GB available"

    # Check Docker container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        error "TimescaleDB container '${CONTAINER_NAME}' is not running"
    fi
    log "INFO" "Container check passed: ${CONTAINER_NAME} is running"

    # Check database connectivity
    if ! docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
        error "Database is not ready"
    fi
    log "INFO" "Database connectivity check passed"
}

perform_backup() {
    log "INFO" "Starting backup: $BACKUP_FILE"

    # Perform backup using docker exec
    log "INFO" "Executing pg_dump..."

    # Use custom format for flexibility, then compress
    if docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
        pg_dump -U "$DB_USER" -d "$DB_NAME" \
        --format=plain \
        --no-owner \
        --no-privileges \
        --verbose \
        2>> "$LOG_FILE" | gzip -"$COMPRESSION_LEVEL" > "$BACKUP_PATH"; then

        log "INFO" "Backup completed successfully"
    else
        error "pg_dump failed"
    fi

    # Get backup file size
    local backup_size=$(du -h "$BACKUP_PATH" | cut -f1)
    log "INFO" "Backup size: $backup_size"

    # Verify backup is not empty
    local backup_bytes=$(stat -c%s "$BACKUP_PATH")
    if [ "$backup_bytes" -lt 1024 ]; then
        error "Backup file is suspiciously small: $backup_bytes bytes"
    fi
}

verify_backup() {
    log "INFO" "Verifying backup integrity..."

    # Calculate checksum
    local checksum=$(md5sum "$BACKUP_PATH" | cut -d' ' -f1)
    echo "$checksum" > "${BACKUP_PATH}.md5"
    log "INFO" "Backup checksum: $checksum"

    # Test gzip integrity
    if gzip -t "$BACKUP_PATH" 2>/dev/null; then
        log "INFO" "Backup compression integrity verified"
    else
        error "Backup file is corrupted (gzip test failed)"
    fi

    # Quick content check - verify it contains SQL dump header
    local content_check=$(zcat "$BACKUP_PATH" 2>/dev/null | head -n 20 | grep -i "PostgreSQL" || echo "")
    if [ -n "$content_check" ]; then
        log "INFO" "Backup content verification passed"
    else
        log "WARN" "Could not verify backup content (non-fatal)"
    fi
}

upload_to_azure() {
    if [ -z "$AZURE_ACCOUNT" ]; then
        log "INFO" "Azure storage not configured, skipping upload"
        return 0
    fi

    log "INFO" "Uploading to Azure Blob Storage..."

    # Check if Azure CLI is available
    if ! command -v az &> /dev/null; then
        log "WARN" "Azure CLI not installed, skipping upload"
        return 0
    fi

    # Upload to Azure
    local blob_name="backups/${BACKUP_FILE}"

    if az storage blob upload \
        --account-name "$AZURE_ACCOUNT" \
        --container-name "$AZURE_CONTAINER" \
        --name "$blob_name" \
        --file "$BACKUP_PATH" \
        --tier Cool \
        --metadata "timestamp=$TIMESTAMP" "checksum=$(cat ${BACKUP_PATH}.md5)" \
        --output none 2>> "$LOG_FILE"; then

        log "INFO" "Successfully uploaded to Azure: $blob_name"
    else
        log "ERROR" "Failed to upload to Azure (non-fatal)"
        return 1
    fi
}

cleanup_old_backups() {
    log "INFO" "Cleaning up backups older than $RETENTION_DAYS days..."

    local deleted_count=0

    # Find and delete old backups
    while IFS= read -r -d '' file; do
        log "INFO" "Deleting old backup: $(basename "$file")"
        rm -f "$file" "${file}.md5"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR" -name "timescaledb_backup_*.sql.gz" -type f -mtime "+$RETENTION_DAYS" -print0)

    if [ "$deleted_count" -gt 0 ]; then
        log "INFO" "Deleted $deleted_count old backup(s)"
    else
        log "INFO" "No old backups to delete"
    fi
}

record_metrics() {
    log "INFO" "Recording backup metrics..."

    # Create metrics file for Prometheus or monitoring
    local metrics_file="${BACKUP_DIR}/backup_metrics.txt"

    cat > "$metrics_file" << EOF
# Backup Metrics
# Last updated: $(date -Iseconds)

last_backup_timestamp=$(date +%s)
last_backup_size=$(stat -c%s "$BACKUP_PATH")
last_backup_success=1
backup_duration_seconds=$SECONDS
EOF

    log "INFO" "Metrics recorded to: $metrics_file"
}

send_notification() {
    local status="$1"
    local message="$2"

    # For now, just log. In production, integrate with alerting system
    log "NOTIFY" "[$status] $message"

    # TODO: Integrate with email, Slack, or monitoring system
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "INFO" "==================================================================="
    log "INFO" "TimescaleDB Automated Backup Started"
    log "INFO" "==================================================================="

    # Track execution time
    local start_time=$SECONDS

    # Run backup process
    if check_prerequisites "$@" && \
       perform_backup && \
       verify_backup && \
       cleanup_old_backups && \
       record_metrics; then

        # Try Azure upload (non-fatal)
        upload_to_azure || true

        # Calculate duration
        local duration=$((SECONDS - start_time))

        log "INFO" "==================================================================="
        log "INFO" "Backup completed successfully in ${duration} seconds"
        log "INFO" "Backup file: $BACKUP_PATH"
        log "INFO" "==================================================================="

        send_notification "SUCCESS" "Backup completed: $BACKUP_FILE"
        exit 0
    else
        local duration=$((SECONDS - start_time))
        log "ERROR" "==================================================================="
        log "ERROR" "Backup failed after ${duration} seconds"
        log "ERROR" "==================================================================="

        send_notification "FAILURE" "Backup failed: check $LOG_FILE for details"
        exit 1
    fi
}

# Run main function
main "$@"

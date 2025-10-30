#!/usr/bin/env python3
"""
Data Retention Manager
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 7

Manages data retention policies including:
- Policy execution
- Data archival
- Automated cleanup
- Compliance reporting

Author: INSA Automation Corp
Date: October 28, 2025
"""

import logging
import json
import gzip
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor, Json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetentionManagerException(Exception):
    """Base exception for retention manager errors."""
    pass


class RetentionManager:
    """
    Manages data retention policies and execution.

    Features:
    - Execute retention policies
    - Archive data before deletion
    - Track execution history
    - Generate compliance reports
    """

    def __init__(self, db_config: Dict[str, Any], archive_base_path: str = "/tmp/insa-iiot/archives"):
        """
        Initialize retention manager.

        Args:
            db_config: Database configuration dictionary
            archive_base_path: Base directory for archived data
        """
        self.db_config = db_config
        self.archive_base_path = Path(archive_base_path)

        # Create archive directory if it doesn't exist
        self.archive_base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"RetentionManager initialized - archive path: {self.archive_base_path}")

    def __enter__(self):
        """Context manager entry."""
        self.conn = psycopg2.connect(**self.db_config)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if hasattr(self, 'conn'):
            self.conn.close()

    def list_policies(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        List all retention policies.

        Args:
            enabled_only: If True, only return enabled policies

        Returns:
            List of policy dictionaries
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = "SELECT * FROM retention_policies WHERE 1=1"
            params = []

            if enabled_only:
                query += " AND enabled = %s"
                params.append(True)

            query += " ORDER BY retention_days ASC"

            cursor.execute(query, params)
            policies = cursor.fetchall()

        return [dict(p) for p in policies]

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific retention policy.

        Args:
            policy_id: Policy UUID

        Returns:
            Policy dictionary or None if not found
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM retention_policies WHERE id = %s",
                (policy_id,)
            )
            policy = cursor.fetchone()

        return dict(policy) if policy else None

    def execute_policy(self, policy_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute a retention policy.

        Args:
            policy_id: Policy UUID
            dry_run: If True, simulate execution without deleting data

        Returns:
            Execution results dictionary
        """
        policy = self.get_policy(policy_id)
        if not policy:
            raise RetentionManagerException(f"Policy not found: {policy_id}")

        if not policy['enabled']:
            raise RetentionManagerException(f"Policy is disabled: {policy['name']}")

        # Create execution record
        execution_id = self._create_execution_record(policy_id)

        try:
            logger.info(f"Executing retention policy: {policy['name']} (dry_run={dry_run})")

            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=policy['retention_days'])

            # Execute based on data type
            if policy['data_type'] == 'telemetry':
                result = self._cleanup_telemetry(policy, cutoff_date, dry_run)
            elif policy['data_type'] == 'alerts':
                result = self._cleanup_alerts(policy, cutoff_date, dry_run)
            elif policy['data_type'] == 'audit_logs':
                result = self._cleanup_audit_logs(policy, cutoff_date, dry_run)
            elif policy['data_type'] == 'ml_anomalies':
                result = self._cleanup_ml_anomalies(policy, cutoff_date, dry_run)
            elif policy['data_type'] == 'all':
                # Execute all cleanup operations
                result = self._cleanup_all(policy, cutoff_date, dry_run)
            else:
                raise RetentionManagerException(f"Unknown data type: {policy['data_type']}")

            # Update execution record
            self._complete_execution_record(
                execution_id,
                'success',
                result['records_deleted'],
                result['records_archived'],
                result['bytes_freed']
            )

            # Update policy statistics
            if not dry_run:
                self._update_policy_stats(policy_id, result)

            logger.info(
                f"Policy execution complete: {result['records_deleted']} deleted, "
                f"{result['records_archived']} archived, {result['bytes_freed']} bytes freed"
            )

            return {
                'execution_id': execution_id,
                'policy_id': policy_id,
                'policy_name': policy['name'],
                'status': 'success',
                'dry_run': dry_run,
                **result
            }

        except Exception as e:
            logger.error(f"Error executing policy {policy['name']}: {e}")
            self._complete_execution_record(
                execution_id,
                'failed',
                0, 0, 0,
                error_message=str(e)
            )
            raise

    def _cleanup_telemetry(
        self,
        policy: Dict[str, Any],
        cutoff_date: datetime,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Clean up telemetry data based on policy."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Count records to be cleaned
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM telemetry
                WHERE timestamp < %s
            """, (cutoff_date,))

            count = cursor.fetchone()['count']

            if count == 0:
                return {'records_deleted': 0, 'records_archived': 0, 'bytes_freed': 0}

            # Archive if configured
            archived_count = 0
            if policy['archive_before_delete'] and not dry_run:
                archived_count = self._archive_telemetry(policy, cutoff_date)

            # Delete records
            deleted_count = 0
            if not dry_run:
                cursor.execute("""
                    DELETE FROM telemetry
                    WHERE timestamp < %s
                """, (cutoff_date,))
                deleted_count = cursor.rowcount
                self.conn.commit()
            else:
                deleted_count = count

            # Estimate bytes freed (rough estimate: 200 bytes per record)
            bytes_freed = deleted_count * 200

            return {
                'records_deleted': deleted_count,
                'records_archived': archived_count,
                'bytes_freed': bytes_freed
            }

    def _cleanup_alerts(
        self,
        policy: Dict[str, Any],
        cutoff_date: datetime,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Clean up alerts based on policy and filter criteria."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build query with filter criteria
            query = "SELECT COUNT(*) as count FROM alerts WHERE created_at < %s"
            params = [cutoff_date]

            # Apply filter criteria (e.g., only delete low-severity alerts)
            if policy['filter_criteria']:
                if 'severity' in policy['filter_criteria']:
                    severities = policy['filter_criteria']['severity']
                    query += " AND severity = ANY(%s)"
                    params.append(severities)

            cursor.execute(query, params)
            count = cursor.fetchone()['count']

            if count == 0:
                return {'records_deleted': 0, 'records_archived': 0, 'bytes_freed': 0}

            # Archive if configured
            archived_count = 0
            if policy['archive_before_delete'] and not dry_run:
                archived_count = self._archive_alerts(policy, cutoff_date)

            # Delete records
            deleted_count = 0
            if not dry_run:
                delete_query = "DELETE FROM alerts WHERE created_at < %s"
                delete_params = [cutoff_date]

                if policy['filter_criteria'] and 'severity' in policy['filter_criteria']:
                    delete_query += " AND severity = ANY(%s)"
                    delete_params.append(policy['filter_criteria']['severity'])

                cursor.execute(delete_query, delete_params)
                deleted_count = cursor.rowcount
                self.conn.commit()
            else:
                deleted_count = count

            bytes_freed = deleted_count * 500  # Estimate: 500 bytes per alert

            return {
                'records_deleted': deleted_count,
                'records_archived': archived_count,
                'bytes_freed': bytes_freed
            }

    def _cleanup_audit_logs(
        self,
        policy: Dict[str, Any],
        cutoff_date: datetime,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Clean up audit logs based on policy."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM audit_logs
                WHERE created_at < %s
            """, (cutoff_date,))

            count = cursor.fetchone()['count']

            if count == 0:
                return {'records_deleted': 0, 'records_archived': 0, 'bytes_freed': 0}

            # Archive if configured (audit logs should always be archived for compliance)
            archived_count = 0
            if policy['archive_before_delete'] and not dry_run:
                archived_count = self._archive_audit_logs(policy, cutoff_date)

            # Delete records
            deleted_count = 0
            if not dry_run:
                cursor.execute("""
                    DELETE FROM audit_logs
                    WHERE created_at < %s
                """, (cutoff_date,))
                deleted_count = cursor.rowcount
                self.conn.commit()
            else:
                deleted_count = count

            bytes_freed = deleted_count * 300

            return {
                'records_deleted': deleted_count,
                'records_archived': archived_count,
                'bytes_freed': bytes_freed
            }

    def _cleanup_ml_anomalies(
        self,
        policy: Dict[str, Any],
        cutoff_date: datetime,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Clean up ML anomaly records based on policy."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM ml_anomalies
                WHERE detected_at < %s
            """, (cutoff_date,))

            count = cursor.fetchone()['count']

            if count == 0:
                return {'records_deleted': 0, 'records_archived': 0, 'bytes_freed': 0}

            # Archive if configured
            archived_count = 0
            if policy['archive_before_delete'] and not dry_run:
                archived_count = self._archive_ml_anomalies(policy, cutoff_date)

            # Delete records
            deleted_count = 0
            if not dry_run:
                cursor.execute("""
                    DELETE FROM ml_anomalies
                    WHERE detected_at < %s
                """, (cutoff_date,))
                deleted_count = cursor.rowcount
                self.conn.commit()
            else:
                deleted_count = count

            bytes_freed = deleted_count * 400

            return {
                'records_deleted': deleted_count,
                'records_archived': archived_count,
                'bytes_freed': bytes_freed
            }

    def _cleanup_all(
        self,
        policy: Dict[str, Any],
        cutoff_date: datetime,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Execute cleanup for all data types."""
        total_deleted = 0
        total_archived = 0
        total_bytes = 0

        # Cleanup each data type
        for data_type in ['telemetry', 'alerts', 'audit_logs', 'ml_anomalies']:
            temp_policy = policy.copy()
            temp_policy['data_type'] = data_type

            result = getattr(self, f'_cleanup_{data_type}')(temp_policy, cutoff_date, dry_run)

            total_deleted += result['records_deleted']
            total_archived += result['records_archived']
            total_bytes += result['bytes_freed']

        return {
            'records_deleted': total_deleted,
            'records_archived': total_archived,
            'bytes_freed': total_bytes
        }

    def _archive_telemetry(self, policy: Dict[str, Any], cutoff_date: datetime) -> int:
        """Archive telemetry data to file."""
        return self._archive_data('telemetry', policy, cutoff_date, 'timestamp')

    def _archive_alerts(self, policy: Dict[str, Any], cutoff_date: datetime) -> int:
        """Archive alerts to file."""
        return self._archive_data('alerts', policy, cutoff_date, 'created_at')

    def _archive_audit_logs(self, policy: Dict[str, Any], cutoff_date: datetime) -> int:
        """Archive audit logs to file."""
        return self._archive_data('audit_logs', policy, cutoff_date, 'created_at')

    def _archive_ml_anomalies(self, policy: Dict[str, Any], cutoff_date: datetime) -> int:
        """Archive ML anomalies to file."""
        return self._archive_data('ml_anomalies', policy, cutoff_date, 'detected_at')

    def _archive_data(
        self,
        table_name: str,
        policy: Dict[str, Any],
        cutoff_date: datetime,
        timestamp_col: str
    ) -> int:
        """
        Generic archive function for any table.

        Args:
            table_name: Name of table to archive
            policy: Retention policy
            cutoff_date: Records before this date will be archived
            timestamp_col: Name of timestamp column

        Returns:
            Number of records archived
        """
        # Create archive file path
        archive_dir = self.archive_base_path / table_name
        archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_file = archive_dir / f"{table_name}_{timestamp_str}.jsonl.gz"

        # Fetch data to archive
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = f"SELECT * FROM {table_name} WHERE {timestamp_col} < %s"
            params = [cutoff_date]

            # Apply filter criteria if present
            if policy['filter_criteria'] and 'severity' in policy['filter_criteria']:
                if table_name == 'alerts':
                    query += " AND severity = ANY(%s)"
                    params.append(policy['filter_criteria']['severity'])

            cursor.execute(query, params)
            records = cursor.fetchall()

        if not records:
            return 0

        # Write to compressed JSONL file
        with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
            for record in records:
                # Convert datetime objects to ISO format
                record_dict = dict(record)
                for key, value in record_dict.items():
                    if isinstance(value, datetime):
                        record_dict[key] = value.isoformat()

                f.write(json.dumps(record_dict) + '\n')

        # Calculate checksum
        checksum = self._calculate_checksum(archive_file)

        # Get file size
        file_size = archive_file.stat().st_size

        # Record archive in index
        self._record_archive_index(
            policy['id'],
            table_name,
            str(archive_file),
            len(records),
            file_size,
            checksum,
            min(r[timestamp_col] for r in records),
            max(r[timestamp_col] for r in records)
        )

        logger.info(
            f"Archived {len(records)} {table_name} records to {archive_file} "
            f"({file_size/1024:.1f} KB)"
        )

        return len(records)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _record_archive_index(
        self,
        policy_id: str,
        data_type: str,
        archive_path: str,
        record_count: int,
        file_size: int,
        checksum: str,
        start_date: datetime,
        end_date: datetime
    ):
        """Record archive in index table."""
        with self.conn.cursor() as cursor:
            # Get current execution_id (latest for this policy)
            cursor.execute("""
                SELECT id FROM retention_executions
                WHERE policy_id = %s
                ORDER BY started_at DESC
                LIMIT 1
            """, (policy_id,))

            execution_row = cursor.fetchone()
            execution_id = execution_row[0] if execution_row else None

            cursor.execute("""
                INSERT INTO archived_data_index (
                    policy_id, execution_id, data_type, archive_path,
                    archive_format, compression, data_start_date,
                    data_end_date, record_count, file_size_bytes, checksum
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                policy_id, execution_id, data_type, archive_path,
                'jsonl', 'gzip', start_date, end_date,
                record_count, file_size, checksum
            ))

        self.conn.commit()

    def _create_execution_record(self, policy_id: str) -> str:
        """Create execution record and return execution_id."""
        import uuid

        execution_id = str(uuid.uuid4())

        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO retention_executions (
                    id, policy_id, started_at, status
                )
                VALUES (%s, %s, NOW(), 'running')
                RETURNING id
            """, (execution_id, policy_id))

        self.conn.commit()
        return execution_id

    def _complete_execution_record(
        self,
        execution_id: str,
        status: str,
        records_deleted: int,
        records_archived: int,
        bytes_freed: int,
        error_message: Optional[str] = None
    ):
        """Update execution record with completion details."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE retention_executions
                SET
                    completed_at = NOW(),
                    status = %s,
                    records_deleted = %s,
                    records_archived = %s,
                    bytes_freed = %s,
                    error_message = %s
                WHERE id = %s
            """, (
                status,
                records_deleted,
                records_archived,
                bytes_freed,
                error_message,
                execution_id
            ))

        self.conn.commit()

    def _update_policy_stats(self, policy_id: str, result: Dict[str, Any]):
        """Update policy statistics."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE retention_policies
                SET
                    last_executed_at = NOW(),
                    last_execution_status = 'success',
                    total_records_deleted = total_records_deleted + %s,
                    total_records_archived = total_records_archived + %s,
                    total_bytes_freed = total_bytes_freed + %s
                WHERE id = %s
            """, (
                result['records_deleted'],
                result['records_archived'],
                result['bytes_freed'],
                policy_id
            ))

        self.conn.commit()

    def get_execution_history(
        self,
        policy_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get execution history.

        Args:
            policy_id: Filter by policy (optional)
            limit: Maximum results

        Returns:
            List of execution records
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    re.*,
                    rp.name as policy_name
                FROM retention_executions re
                JOIN retention_policies rp ON re.policy_id = rp.id
                WHERE 1=1
            """
            params = []

            if policy_id:
                query += " AND re.policy_id = %s"
                params.append(policy_id)

            query += " ORDER BY re.started_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            executions = cursor.fetchall()

        return [dict(e) for e in executions]

    def get_archived_data_index(
        self,
        data_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get archived data index.

        Args:
            data_type: Filter by data type (optional)
            limit: Maximum results

        Returns:
            List of archived data records
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = "SELECT * FROM archived_data_index WHERE 1=1"
            params = []

            if data_type:
                query += " AND data_type = %s"
                params.append(data_type)

            query += " ORDER BY archived_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            archives = cursor.fetchall()

        return [dict(a) for a in archives]


# =============================================================================
# Example usage
# =============================================================================

if __name__ == '__main__':
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'insa_iiot',
        'user': 'iiot_user',
        'password': 'iiot_secure_2025'
    }

    print("=== Data Retention Manager ===\n")

    with RetentionManager(DB_CONFIG) as manager:
        # List all policies
        policies = manager.list_policies()
        print(f"Active Retention Policies: {len(policies)}")
        for policy in policies:
            print(f"  - {policy['name']}: {policy['retention_days']} days ({policy['data_type']})")

        print("\n✓ Retention Manager ready")

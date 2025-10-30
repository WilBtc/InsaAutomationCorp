#!/usr/bin/env python3
"""
Alert Grouping and Deduplication Manager
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8

Purpose:
- Group similar alerts to reduce noise (70%+ reduction target)
- Deduplicate identical alerts from same source
- Track group statistics and metrics
- Provide noise reduction analytics

Grouping Strategy:
- Composite key: device_id + rule_id + severity
- Time window: 5 minutes (configurable)
- Auto-close when condition resolved

Usage:
    from alert_grouping import AlertGroupManager

    with AlertGroupManager(DB_CONFIG) as manager:
        # Find or create group for new alert
        group_id = manager.find_or_create_group(
            device_id='device-uuid',
            rule_id='rule-uuid',
            severity='critical',
            alert_id='alert-uuid'
        )

        # Get group statistics
        stats = manager.get_group_statistics(group_id)
        print(f"Noise reduction: {stats['noise_reduction_pct']}%")

        # Close group when resolved
        manager.close_group(group_id)

Author: INSA Automation Corp
Date: October 28, 2025
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor, Json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertGroupException(Exception):
    """Base exception for alert grouping errors"""
    pass


class GroupNotFound(AlertGroupException):
    """Raised when alert group is not found"""
    pass


class InvalidGroupKey(AlertGroupException):
    """Raised when group key format is invalid"""
    pass


class AlertGroupManager:
    """
    Manages alert grouping and deduplication.

    Provides methods to:
    - Create and manage alert groups
    - Find or create groups for new alerts
    - Track group statistics and metrics
    - Calculate noise reduction percentages
    - Query active and historical groups

    The manager automatically groups alerts by device, rule, and severity
    within a configurable time window (default 5 minutes).
    """

    def __init__(self, db_config: Dict[str, Any], time_window_minutes: int = 5):
        """
        Initialize Alert Group Manager.

        Args:
            db_config: Database configuration dictionary with keys:
                      host, port, database, user, password
            time_window_minutes: Grouping time window in minutes (default: 5)
        """
        self.db_config = db_config
        self.time_window_minutes = time_window_minutes
        self.conn = None
        logger.info(f"Initializing AlertGroupManager (time_window={time_window_minutes}min)")

    def __enter__(self):
        """Context manager entry"""
        self.conn = psycopg2.connect(**self.db_config)
        logger.info("Database connection established")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def _generate_group_key(self, device_id: str, rule_id: str, severity: str) -> str:
        """
        Generate composite group key.

        Args:
            device_id: Device UUID
            rule_id: Rule UUID
            severity: Alert severity

        Returns:
            Composite key string (device_id:rule_id:severity)
        """
        return f"{device_id}:{rule_id}:{severity}"

    def find_or_create_group(
        self,
        device_id: str,
        rule_id: str,
        severity: str,
        alert_id: str
    ) -> str:
        """
        Find existing group or create new one for alert.

        This is the main method for alert grouping. It checks if an active
        group exists within the time window. If yes, adds alert to group.
        If no, creates new group.

        Args:
            device_id: Device UUID
            rule_id: Rule UUID
            severity: Alert severity
            alert_id: Alert UUID to add to group

        Returns:
            Group UUID (existing or newly created)

        Example:
            group_id = manager.find_or_create_group(
                device_id='device-123',
                rule_id='rule-456',
                severity='critical',
                alert_id='alert-789'
            )
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT find_or_create_alert_group(%s, %s, %s, %s, %s)
                    AS group_id
                """, (device_id, rule_id, severity, alert_id, self.time_window_minutes))

                result = cursor.fetchone()
                group_id = result['group_id']

            self.conn.commit()
            logger.info(f"Alert {alert_id} added to group {group_id}")
            return group_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error finding/creating group: {e}")
            raise AlertGroupException(f"Failed to find/create group: {e}")

    def create_group(
        self,
        device_id: str,
        rule_id: str,
        severity: str,
        representative_alert_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create new alert group explicitly.

        Args:
            device_id: Device UUID
            rule_id: Rule UUID
            severity: Alert severity
            representative_alert_id: First alert in group
            metadata: Optional metadata dictionary

        Returns:
            New group UUID

        Example:
            group_id = manager.create_group(
                device_id='device-123',
                rule_id='rule-456',
                severity='critical',
                representative_alert_id='alert-789',
                metadata={'source': 'temperature_sensor'}
            )
        """
        group_key = self._generate_group_key(device_id, rule_id, severity)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO alert_groups (
                        device_id, rule_id, severity, group_key,
                        first_occurrence_at, last_occurrence_at,
                        occurrence_count, status,
                        representative_alert_id, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    device_id,
                    rule_id,
                    severity,
                    group_key,
                    datetime.now(),
                    datetime.now(),
                    1,
                    'active',
                    representative_alert_id,
                    Json(metadata or {})
                ))

                group_id = cursor.fetchone()['id']

            self.conn.commit()
            logger.info(f"Created new group {group_id} with key {group_key}")
            return group_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating group: {e}")
            raise AlertGroupException(f"Failed to create group: {e}")

    def add_to_group(self, group_id: str, alert_id: str) -> Dict[str, Any]:
        """
        Add alert to existing group.

        Updates occurrence count and last occurrence timestamp.

        Args:
            group_id: Group UUID
            alert_id: Alert UUID to add

        Returns:
            Updated group dictionary

        Example:
            updated_group = manager.add_to_group(
                group_id='group-123',
                alert_id='alert-789'
            )
            print(f"Group now has {updated_group['occurrence_count']} alerts")
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Update group
                cursor.execute("""
                    UPDATE alert_groups
                    SET occurrence_count = occurrence_count + 1,
                        last_occurrence_at = NOW()
                    WHERE id = %s
                    RETURNING *
                """, (group_id,))

                group = cursor.fetchone()
                if not group:
                    raise GroupNotFound(f"Group {group_id} not found")

                # Update alert to reference group
                cursor.execute("""
                    UPDATE alerts
                    SET grouped_alert_id = %s
                    WHERE id = %s
                """, (group_id, alert_id))

            self.conn.commit()
            logger.info(f"Added alert {alert_id} to group {group_id} "
                       f"(count: {group['occurrence_count']})")
            return dict(group)

        except GroupNotFound:
            self.conn.rollback()
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error adding alert to group: {e}")
            raise AlertGroupException(f"Failed to add alert to group: {e}")

    def get_group(self, group_id: str) -> Dict[str, Any]:
        """
        Get group by ID.

        Args:
            group_id: Group UUID

        Returns:
            Group dictionary

        Raises:
            GroupNotFound: If group doesn't exist
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM alert_groups WHERE id = %s
                """, (group_id,))

                group = cursor.fetchone()
                if not group:
                    raise GroupNotFound(f"Group {group_id} not found")

                return dict(group)

        except GroupNotFound:
            raise
        except Exception as e:
            logger.error(f"Error getting group: {e}")
            raise AlertGroupException(f"Failed to get group: {e}")

    def get_group_by_key(
        self,
        device_id: str,
        rule_id: str,
        severity: str,
        active_only: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Find active group by composite key.

        Args:
            device_id: Device UUID
            rule_id: Rule UUID
            severity: Alert severity
            active_only: Only return active groups (default: True)

        Returns:
            Group dictionary or None if not found

        Example:
            group = manager.get_group_by_key(
                device_id='device-123',
                rule_id='rule-456',
                severity='critical'
            )
        """
        group_key = self._generate_group_key(device_id, rule_id, severity)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if active_only:
                    cursor.execute("""
                        SELECT * FROM alert_groups
                        WHERE group_key = %s AND status = 'active'
                        ORDER BY last_occurrence_at DESC
                        LIMIT 1
                    """, (group_key,))
                else:
                    cursor.execute("""
                        SELECT * FROM alert_groups
                        WHERE group_key = %s
                        ORDER BY last_occurrence_at DESC
                        LIMIT 1
                    """, (group_key,))

                group = cursor.fetchone()
                return dict(group) if group else None

        except Exception as e:
            logger.error(f"Error finding group by key: {e}")
            raise AlertGroupException(f"Failed to find group by key: {e}")

    def close_group(self, group_id: str) -> Dict[str, Any]:
        """
        Close alert group.

        Marks group as closed when condition is resolved.

        Args:
            group_id: Group UUID

        Returns:
            Updated group dictionary

        Example:
            closed_group = manager.close_group('group-123')
            print(f"Closed group with {closed_group['occurrence_count']} alerts")
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    UPDATE alert_groups
                    SET status = 'closed'
                    WHERE id = %s
                    RETURNING *
                """, (group_id,))

                group = cursor.fetchone()
                if not group:
                    raise GroupNotFound(f"Group {group_id} not found")

            self.conn.commit()
            logger.info(f"Closed group {group_id} ({group['occurrence_count']} alerts)")
            return dict(group)

        except GroupNotFound:
            self.conn.rollback()
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error closing group: {e}")
            raise AlertGroupException(f"Failed to close group: {e}")

    def get_active_groups(
        self,
        device_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query active alert groups.

        Args:
            device_id: Filter by device UUID (optional)
            severity: Filter by severity (optional)
            limit: Maximum number of results (default: 100)

        Returns:
            List of group dictionaries

        Example:
            # Get all active critical groups
            groups = manager.get_active_groups(severity='critical')

            # Get active groups for specific device
            groups = manager.get_active_groups(device_id='device-123')
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM v_active_alert_groups
                    WHERE 1=1
                """
                params = []

                if device_id:
                    query += " AND device_id = %s"
                    params.append(device_id)

                if severity:
                    query += " AND severity = %s"
                    params.append(severity)

                query += " ORDER BY last_occurrence_at DESC LIMIT %s"
                params.append(limit)

                cursor.execute(query, params)
                groups = cursor.fetchall()

                return [dict(group) for group in groups]

        except Exception as e:
            logger.error(f"Error querying active groups: {e}")
            raise AlertGroupException(f"Failed to query active groups: {e}")

    def get_group_statistics(self, group_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a group.

        Args:
            group_id: Group UUID

        Returns:
            Statistics dictionary with keys:
                - group_id
                - device_name
                - rule_name
                - severity
                - occurrence_count
                - first_occurrence
                - last_occurrence
                - age_minutes
                - noise_reduction_pct
                - status

        Example:
            stats = manager.get_group_statistics('group-123')
            print(f"Group: {stats['device_name']} - {stats['rule_name']}")
            print(f"Alerts: {stats['occurrence_count']}")
            print(f"Noise reduction: {stats['noise_reduction_pct']}%")
            print(f"Age: {stats['age_minutes']} minutes")
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM get_group_statistics(%s)
                """, (group_id,))

                stats = cursor.fetchone()
                if not stats:
                    raise GroupNotFound(f"Group {group_id} not found")

                return dict(stats)

        except GroupNotFound:
            raise
        except Exception as e:
            logger.error(f"Error getting group statistics: {e}")
            raise AlertGroupException(f"Failed to get group statistics: {e}")

    def get_overall_statistics(self) -> Dict[str, Any]:
        """
        Get platform-wide grouping statistics.

        Returns:
            Statistics dictionary with keys:
                - total_groups: Total number of groups
                - active_groups: Number of active groups
                - closed_groups: Number of closed groups
                - total_alerts_grouped: Total alerts across all groups
                - avg_alerts_per_group: Average alerts per group
                - max_alerts_in_group: Maximum alerts in a single group
                - overall_noise_reduction_pct: Overall noise reduction %

        Example:
            stats = manager.get_overall_statistics()
            print(f"Total groups: {stats['total_groups']}")
            print(f"Active: {stats['active_groups']}")
            print(f"Alerts grouped: {stats['total_alerts_grouped']}")
            print(f"Noise reduction: {stats['overall_noise_reduction_pct']}%")
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM v_alert_group_stats")
                stats = cursor.fetchone()

                return dict(stats) if stats else {
                    'total_groups': 0,
                    'active_groups': 0,
                    'closed_groups': 0,
                    'total_alerts_grouped': 0,
                    'avg_alerts_per_group': 0,
                    'max_alerts_in_group': 0,
                    'overall_noise_reduction_pct': 0
                }

        except Exception as e:
            logger.error(f"Error getting overall statistics: {e}")
            raise AlertGroupException(f"Failed to get overall statistics: {e}")

    def get_groups_for_device(
        self,
        device_id: str,
        active_only: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all groups for a specific device.

        Args:
            device_id: Device UUID
            active_only: Only return active groups (default: True)
            limit: Maximum number of results (default: 50)

        Returns:
            List of group dictionaries

        Example:
            groups = manager.get_groups_for_device('device-123')
            for group in groups:
                print(f"{group['rule_name']}: {group['occurrence_count']} alerts")
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if active_only:
                    cursor.execute("""
                        SELECT * FROM alert_groups
                        WHERE device_id = %s AND status = 'active'
                        ORDER BY last_occurrence_at DESC
                        LIMIT %s
                    """, (device_id, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM alert_groups
                        WHERE device_id = %s
                        ORDER BY last_occurrence_at DESC
                        LIMIT %s
                    """, (device_id, limit))

                groups = cursor.fetchall()
                return [dict(group) for group in groups]

        except Exception as e:
            logger.error(f"Error getting groups for device: {e}")
            raise AlertGroupException(f"Failed to get groups for device: {e}")

    def update_group_metadata(
        self,
        group_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update group metadata.

        Args:
            group_id: Group UUID
            metadata: Metadata dictionary to merge

        Returns:
            Updated group dictionary

        Example:
            manager.update_group_metadata(
                group_id='group-123',
                metadata={'escalated': True, 'escalated_at': '2025-10-28T10:00:00Z'}
            )
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get current metadata
                cursor.execute("""
                    SELECT metadata FROM alert_groups WHERE id = %s
                """, (group_id,))

                result = cursor.fetchone()
                if not result:
                    raise GroupNotFound(f"Group {group_id} not found")

                # Merge metadata
                current_metadata = result['metadata'] or {}
                updated_metadata = {**current_metadata, **metadata}

                # Update
                cursor.execute("""
                    UPDATE alert_groups
                    SET metadata = %s
                    WHERE id = %s
                    RETURNING *
                """, (Json(updated_metadata), group_id))

                group = cursor.fetchone()

            self.conn.commit()
            logger.info(f"Updated metadata for group {group_id}")
            return dict(group)

        except GroupNotFound:
            self.conn.rollback()
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating group metadata: {e}")
            raise AlertGroupException(f"Failed to update group metadata: {e}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


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

    print("=== Alert Grouping and Deduplication Manager ===\n")

    # Example 1: Find or create group
    print("Example 1: Find or create group")
    with AlertGroupManager(DB_CONFIG) as manager:
        # Simulate new alert
        group_id = manager.find_or_create_group(
            device_id='sample-device-uuid',
            rule_id='sample-rule-uuid',
            severity='critical',
            alert_id='sample-alert-uuid'
        )
        print(f"Alert added to group: {group_id}")

    # Example 2: Get overall statistics
    print("\nExample 2: Overall statistics")
    with AlertGroupManager(DB_CONFIG) as manager:
        stats = manager.get_overall_statistics()
        print(f"Total groups: {stats['total_groups']}")
        print(f"Active groups: {stats['active_groups']}")
        print(f"Total alerts grouped: {stats['total_alerts_grouped']}")
        print(f"Noise reduction: {stats['overall_noise_reduction_pct']}%")

    # Example 3: Query active groups
    print("\nExample 3: Active critical groups")
    with AlertGroupManager(DB_CONFIG) as manager:
        groups = manager.get_active_groups(severity='critical', limit=5)
        print(f"Found {len(groups)} active critical groups")
        for group in groups:
            print(f"  - Group {group['id']}: {group['occurrence_count']} alerts "
                  f"(noise reduction: {group.get('noise_reduction_pct', 0)}%)")

    print("\n✓ Alert grouping manager initialized successfully")

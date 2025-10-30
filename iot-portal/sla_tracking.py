#!/usr/bin/env python3
"""
SLA Tracking Module
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8: Advanced Alerting

Tracks and enforces Service Level Agreements (SLAs) for alert response:
- Time to Acknowledge (TTA): How quickly alerts are acknowledged
- Time to Resolve (TTR): How quickly alerts are resolved
- SLA Breach Detection: Automatic detection of missed SLA targets
- Compliance Reporting: SLA performance metrics

SLA Targets by Severity:
- critical: TTA 5min, TTR 30min
- high: TTA 15min, TTR 120min (2h)
- medium: TTA 60min, TTR 480min (8h)
- low: TTA 240min, TTR 1440min (24h)
- info: TTA 1440min, TTR 10080min (1 week)

Features:
- Auto-calculation of TTA/TTR from state changes
- Real-time breach detection
- Compliance reporting by severity/time period
- Integration with alert state machine

Author: INSA Automation Corp
Created: October 28, 2025
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SLAException(Exception):
    """Base exception for SLA tracking errors"""
    pass


class SLANotFound(SLAException):
    """Raised when SLA record does not exist"""
    pass


class SLATracker:
    """
    SLA Tracking System

    Tracks alert response times and detects SLA breaches.

    Responsibilities:
    1. Calculate TTA when alert is acknowledged
    2. Calculate TTR when alert is resolved
    3. Detect SLA breaches (TTA/TTR exceeds targets)
    4. Generate compliance reports

    Database Schema:
        Table: alert_slas
        - alert_id: UUID (foreign key to alerts, unique)
        - severity: VARCHAR(20)
        - tta_target: INTEGER (minutes)
        - ttr_target: INTEGER (minutes)
        - tta_actual: INTEGER (minutes, nullable)
        - ttr_actual: INTEGER (minutes, nullable)
        - tta_breached: BOOLEAN (default FALSE)
        - ttr_breached: BOOLEAN (default FALSE)
        - created_at: TIMESTAMP (alert creation time)
        - acknowledged_at: TIMESTAMP (nullable)
        - resolved_at: TIMESTAMP (nullable)

    Example Usage:
        >>> from sla_tracking import SLATracker
        >>>
        >>> # Initialize
        >>> tracker = SLATracker(db_config)
        >>>
        >>> # Update TTA when alert is acknowledged
        >>> tracker.update_tta(alert_id='123...')
        >>>
        >>> # Update TTR when alert is resolved
        >>> tracker.update_ttr(alert_id='123...')
        >>>
        >>> # Get SLA status
        >>> sla = tracker.get_sla_status(alert_id='123...')
        >>> print(f"TTA: {sla['tta_actual']}min (target: {sla['tta_target']}min)")
        >>> print(f"Breached: {sla['tta_breached']}")
        >>>
        >>> # Get compliance report
        >>> report = tracker.get_compliance_report(severity='critical')
        >>> print(f"Critical alerts: {report['total_alerts']}")
        >>> print(f"TTA compliance: {report['tta_compliance_rate']}%")
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize SLA Tracker

        Args:
            db_config: PostgreSQL connection configuration
                {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'insa_iiot',
                    'user': 'iiot_user',
                    'password': 'password'
                }
        """
        self.db_config = db_config
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("SLA Tracker: Database connection established")
        except psycopg2.Error as e:
            logger.error(f"SLA Tracker: Database connection failed: {e}")
            raise SLAException(f"Failed to connect to database: {e}")

    def _ensure_connection(self):
        """Ensure database connection is alive"""
        if self.conn is None or self.conn.closed:
            self._connect()

    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("SLA Tracker: Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def get_sla_status(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Get SLA status for an alert

        Args:
            alert_id: UUID of the alert

        Returns:
            Dictionary with SLA details:
            {
                'alert_id': 'uuid',
                'severity': 'critical',
                'tta_target': 5,
                'ttr_target': 30,
                'tta_actual': 3,
                'ttr_actual': 25,
                'tta_breached': False,
                'ttr_breached': False,
                'created_at': datetime,
                'acknowledged_at': datetime,
                'resolved_at': datetime
            }

            Returns None if SLA record does not exist

        Raises:
            SLAException: On database errors
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT *
                    FROM alert_slas
                    WHERE alert_id = %s
                """, (alert_id,))

                return cursor.fetchone()

        except psycopg2.Error as e:
            logger.error(f"Failed to get SLA status for alert {alert_id}: {e}")
            raise SLAException(f"Database error: {e}")

    def update_tta(self, alert_id: str) -> Dict[str, Any]:
        """
        Update Time to Acknowledge (TTA) for an alert

        Calculates TTA from alert creation time to current time,
        detects breaches, and updates the SLA record.

        Args:
            alert_id: UUID of the alert

        Returns:
            Updated SLA record

        Raises:
            SLANotFound: If SLA record does not exist
            SLAException: On database errors

        Example:
            >>> tracker.update_tta('123...')
            {
                'alert_id': '123...',
                'tta_actual': 3,
                'tta_target': 5,
                'tta_breached': False,
                'acknowledged_at': datetime(...)
            }
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Calculate TTA and update record
                cursor.execute("""
                    UPDATE alert_slas
                    SET tta_actual = EXTRACT(EPOCH FROM (NOW() - created_at)) / 60,
                        acknowledged_at = NOW(),
                        tta_breached = (EXTRACT(EPOCH FROM (NOW() - created_at)) / 60) > tta_target
                    WHERE alert_id = %s
                    RETURNING *
                """, (alert_id,))

                result = cursor.fetchone()

                if result is None:
                    raise SLANotFound(f"SLA record not found for alert {alert_id}")

            self.conn.commit()

            # Log breach if detected
            if result['tta_breached']:
                logger.warning(
                    f"SLA BREACH: Alert {alert_id} TTA {result['tta_actual']:.1f}min "
                    f"exceeded target {result['tta_target']}min (severity: {result['severity']})"
                )
            else:
                logger.info(
                    f"Alert {alert_id}: TTA {result['tta_actual']:.1f}min "
                    f"(target: {result['tta_target']}min, severity: {result['severity']})"
                )

            return result

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to update TTA for alert {alert_id}: {e}")
            raise SLAException(f"Database error: {e}")

    def update_ttr(self, alert_id: str) -> Dict[str, Any]:
        """
        Update Time to Resolve (TTR) for an alert

        Calculates TTR from alert creation time to current time,
        detects breaches, and updates the SLA record.

        Args:
            alert_id: UUID of the alert

        Returns:
            Updated SLA record

        Raises:
            SLANotFound: If SLA record does not exist
            SLAException: On database errors

        Example:
            >>> tracker.update_ttr('123...')
            {
                'alert_id': '123...',
                'ttr_actual': 25,
                'ttr_target': 30,
                'ttr_breached': False,
                'resolved_at': datetime(...)
            }
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Calculate TTR and update record
                cursor.execute("""
                    UPDATE alert_slas
                    SET ttr_actual = EXTRACT(EPOCH FROM (NOW() - created_at)) / 60,
                        resolved_at = NOW(),
                        ttr_breached = (EXTRACT(EPOCH FROM (NOW() - created_at)) / 60) > ttr_target
                    WHERE alert_id = %s
                    RETURNING *
                """, (alert_id,))

                result = cursor.fetchone()

                if result is None:
                    raise SLANotFound(f"SLA record not found for alert {alert_id}")

            self.conn.commit()

            # Log breach if detected
            if result['ttr_breached']:
                logger.warning(
                    f"SLA BREACH: Alert {alert_id} TTR {result['ttr_actual']:.1f}min "
                    f"exceeded target {result['ttr_target']}min (severity: {result['severity']})"
                )
            else:
                logger.info(
                    f"Alert {alert_id}: TTR {result['ttr_actual']:.1f}min "
                    f"(target: {result['ttr_target']}min, severity: {result['severity']})"
                )

            return result

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to update TTR for alert {alert_id}: {e}")
            raise SLAException(f"Database error: {e}")

    def get_compliance_report(
        self,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate SLA compliance report

        Args:
            severity: Filter by severity (critical, high, medium, low, info)
            start_date: Start of reporting period (defaults to 30 days ago)
            end_date: End of reporting period (defaults to now)

        Returns:
            Compliance report:
            {
                'severity': 'critical',  # or 'all' if not filtered
                'total_alerts': 150,
                'acknowledged_alerts': 145,
                'resolved_alerts': 140,
                'tta_compliance_count': 130,
                'tta_compliance_rate': 89.7,  # percentage
                'ttr_compliance_count': 125,
                'ttr_compliance_rate': 89.3,
                'avg_tta': 3.5,  # minutes
                'avg_ttr': 22.1,
                'period_start': datetime,
                'period_end': datetime
            }

        Example:
            >>> report = tracker.get_compliance_report(severity='critical')
            >>> print(f"Critical SLA compliance: {report['tta_compliance_rate']}%")
        """
        self._ensure_connection()

        # Default to last 30 days
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build query with optional severity filter
                query = """
                    SELECT
                        COUNT(*) as total_alerts,
                        COUNT(acknowledged_at) as acknowledged_alerts,
                        COUNT(resolved_at) as resolved_alerts,
                        COUNT(CASE WHEN NOT tta_breached AND acknowledged_at IS NOT NULL THEN 1 END) as tta_compliance_count,
                        COUNT(CASE WHEN NOT ttr_breached AND resolved_at IS NOT NULL THEN 1 END) as ttr_compliance_count,
                        AVG(CASE WHEN tta_actual IS NOT NULL THEN tta_actual END) as avg_tta,
                        AVG(CASE WHEN ttr_actual IS NOT NULL THEN ttr_actual END) as avg_ttr
                    FROM alert_slas
                    WHERE created_at BETWEEN %s AND %s
                """

                params = [start_date, end_date]

                if severity:
                    query += " AND severity = %s"
                    params.append(severity)

                cursor.execute(query, params)
                result = cursor.fetchone()

                # Calculate compliance rates
                tta_compliance_rate = 0.0
                if result['acknowledged_alerts'] > 0:
                    tta_compliance_rate = (result['tta_compliance_count'] / result['acknowledged_alerts']) * 100

                ttr_compliance_rate = 0.0
                if result['resolved_alerts'] > 0:
                    ttr_compliance_rate = (result['ttr_compliance_count'] / result['resolved_alerts']) * 100

                return {
                    'severity': severity or 'all',
                    'total_alerts': result['total_alerts'],
                    'acknowledged_alerts': result['acknowledged_alerts'],
                    'resolved_alerts': result['resolved_alerts'],
                    'tta_compliance_count': result['tta_compliance_count'],
                    'tta_compliance_rate': round(tta_compliance_rate, 1),
                    'ttr_compliance_count': result['ttr_compliance_count'],
                    'ttr_compliance_rate': round(ttr_compliance_rate, 1),
                    'avg_tta': round(float(result['avg_tta'] or 0), 1),
                    'avg_ttr': round(float(result['avg_ttr'] or 0), 1),
                    'period_start': start_date,
                    'period_end': end_date
                }

        except psycopg2.Error as e:
            logger.error(f"Failed to generate compliance report: {e}")
            raise SLAException(f"Database error: {e}")

    def get_breached_alerts(
        self,
        breach_type: str = 'all',
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get list of alerts with SLA breaches

        Args:
            breach_type: Type of breach ('tta', 'ttr', or 'all')
            severity: Filter by severity
            limit: Maximum number of results

        Returns:
            List of breached alert SLA records

        Example:
            >>> breached = tracker.get_breached_alerts(breach_type='tta', severity='critical')
            >>> for alert in breached:
            ...     print(f"Alert {alert['alert_id']}: TTA {alert['tta_actual']}min (target: {alert['tta_target']}min)")
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build query based on breach type
                query = "SELECT * FROM alert_slas WHERE "

                if breach_type == 'tta':
                    query += "tta_breached = TRUE"
                elif breach_type == 'ttr':
                    query += "ttr_breached = TRUE"
                else:  # 'all'
                    query += "(tta_breached = TRUE OR ttr_breached = TRUE)"

                params = []
                if severity:
                    query += " AND severity = %s"
                    params.append(severity)

                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)

                cursor.execute(query, params)
                return cursor.fetchall()

        except psycopg2.Error as e:
            logger.error(f"Failed to get breached alerts: {e}")
            raise SLAException(f"Database error: {e}")

    def get_sla_targets(self, severity: str) -> Tuple[int, int]:
        """
        Get SLA targets for a severity level

        Args:
            severity: Severity level (critical, high, medium, low, info)

        Returns:
            Tuple of (tta_target_minutes, ttr_target_minutes)

        Example:
            >>> tta, ttr = tracker.get_sla_targets('critical')
            >>> print(f"Critical: TTA {tta}min, TTR {ttr}min")
            Critical: TTA 5min, TTR 30min
        """
        # These match the database trigger function
        targets = {
            'critical': (5, 30),
            'high': (15, 120),
            'medium': (60, 480),
            'low': (240, 1440),
            'info': (1440, 10080)
        }

        return targets.get(severity.lower(), (1440, 10080))  # Default to info level


# Integration with Alert State Machine
class SLAIntegratedStateMachine:
    """
    Alert State Machine with automatic SLA tracking

    Wraps the AlertStateMachine to automatically update SLA metrics
    when state changes occur.

    Example:
        >>> from sla_tracking import SLAIntegratedStateMachine
        >>>
        >>> state_machine = SLAIntegratedStateMachine(db_config)
        >>>
        >>> # Acknowledge alert (automatically updates TTA)
        >>> state_machine.acknowledge(alert_id='123...', user_id='456...')
        >>>
        >>> # Resolve alert (automatically updates TTR)
        >>> state_machine.resolve(alert_id='123...', user_id='456...')
    """

    def __init__(self, db_config: Dict[str, Any]):
        """Initialize with integrated SLA tracking"""
        from alert_state_machine import AlertStateMachine

        self.state_machine = AlertStateMachine(db_config)
        self.sla_tracker = SLATracker(db_config)

    def acknowledge(self, alert_id: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Acknowledge alert and update TTA"""
        # Transition state
        result = self.state_machine.acknowledge(alert_id, user_id, **kwargs)

        # Update TTA
        try:
            self.sla_tracker.update_tta(alert_id)
        except Exception as e:
            logger.warning(f"Failed to update TTA for alert {alert_id}: {e}")

        return result

    def resolve(self, alert_id: str, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Resolve alert and update TTR"""
        # Transition state
        result = self.state_machine.resolve(alert_id, user_id, **kwargs)

        # Update TTR
        try:
            self.sla_tracker.update_ttr(alert_id)
        except Exception as e:
            logger.warning(f"Failed to update TTR for alert {alert_id}: {e}")

        return result

    def close(self):
        """Close both connections"""
        self.state_machine.close()
        self.sla_tracker.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example usage
if __name__ == '__main__':
    import os

    # Database configuration
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', 5432),
        'database': os.environ.get('DB_NAME', 'insa_iiot'),
        'user': os.environ.get('DB_USER', 'iiot_user'),
        'password': os.environ.get('DB_PASSWORD', 'iiot_secure_2025')
    }

    # Example: Use standalone SLA tracker
    with SLATracker(DB_CONFIG) as tracker:
        # Get compliance report
        report = tracker.get_compliance_report(severity='critical')
        print(f"\nCritical Alerts SLA Compliance Report:")
        print(f"Total Alerts: {report['total_alerts']}")
        print(f"TTA Compliance: {report['tta_compliance_rate']}%")
        print(f"TTR Compliance: {report['ttr_compliance_rate']}%")
        print(f"Average TTA: {report['avg_tta']} minutes")
        print(f"Average TTR: {report['avg_ttr']} minutes")

        # Get breached alerts
        breached = tracker.get_breached_alerts(breach_type='all', limit=10)
        print(f"\nTotal Breached Alerts: {len(breached)}")

    # Example: Use integrated state machine
    print("\n" + "=" * 70)
    print("Using SLA Integrated State Machine:")
    print("=" * 70)

    try:
        with SLAIntegratedStateMachine(DB_CONFIG) as machine:
            alert_id = '123e4567-e89b-12d3-a456-426614174000'

            # Acknowledge (auto-updates TTA)
            machine.acknowledge(
                alert_id=alert_id,
                user_id='550e8400-e29b-41d4-a716-446655440000',
                notes='Investigating issue'
            )

            # Resolve (auto-updates TTR)
            machine.resolve(
                alert_id=alert_id,
                user_id='550e8400-e29b-41d4-a716-446655440000',
                notes='Issue resolved'
            )

    except Exception as e:
        print(f"Example requires valid alert_id: {e}")

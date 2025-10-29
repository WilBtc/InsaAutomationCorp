#!/usr/bin/env python3
"""
SLA Tracking Database - INSA CRM Platform
Stores SLA compliance data, calculations, and breach history

Database: SQLite (can be migrated to PostgreSQL)
Location: /var/lib/insa-crm/sla_tracking.db
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SLAStatus(Enum):
    """SLA compliance status"""
    EXCELLENT = "excellent"  # >99.9% - Exceeds SLA
    GOOD = "good"  # 99.0-99.9% - Meets SLA
    POOR = "poor"  # 95.0-99.0% - Below SLA
    CRITICAL = "critical"  # <95.0% - Critical violation


class SLASeverity(Enum):
    """SLA severity level"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SLAMeasurement:
    """Single SLA measurement"""
    timestamp: datetime
    sla_name: str
    sla_category: str
    target_value: float
    actual_value: float
    unit: str
    compliant: bool
    status: SLAStatus
    severity: SLASeverity


@dataclass
class SLABreach:
    """SLA breach event"""
    breach_id: int
    sla_name: str
    breach_start: datetime
    breach_end: Optional[datetime]
    duration_seconds: Optional[int]
    target_value: float
    actual_value: float
    severity: SLASeverity
    notified: bool
    resolved: bool


class SLADatabase:
    """SLA tracking database manager"""

    def __init__(self, db_path: str = "/var/lib/insa-crm/sla_tracking.db"):
        """
        Initialize SLA database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self.conn = None
        self._init_database()

        logger.info(f"SLA database initialized at {db_path}")

    def _init_database(self):
        """Create database tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # Table 1: SLA Definitions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sla_definitions (
                sla_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sla_name TEXT NOT NULL UNIQUE,
                sla_category TEXT NOT NULL,
                description TEXT,
                metric_name TEXT NOT NULL,
                target_value REAL NOT NULL,
                unit TEXT NOT NULL,
                severity TEXT NOT NULL,
                percentile INTEGER,
                per_component BOOLEAN DEFAULT 0,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 2: SLA Measurements (time-series data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sla_measurements (
                measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sla_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                actual_value REAL NOT NULL,
                target_value REAL NOT NULL,
                compliant BOOLEAN NOT NULL,
                status TEXT NOT NULL,
                component TEXT,
                FOREIGN KEY (sla_id) REFERENCES sla_definitions(sla_id)
            )
        """)

        # Index for time-series queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_measurements_timestamp
            ON sla_measurements(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_measurements_sla_time
            ON sla_measurements(sla_id, timestamp DESC)
        """)

        # Table 3: SLA Breaches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sla_breaches (
                breach_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sla_id INTEGER NOT NULL,
                breach_start TIMESTAMP NOT NULL,
                breach_end TIMESTAMP,
                duration_seconds INTEGER,
                target_value REAL NOT NULL,
                actual_value REAL NOT NULL,
                severity TEXT NOT NULL,
                notified BOOLEAN DEFAULT 0,
                resolved BOOLEAN DEFAULT 0,
                resolution_notes TEXT,
                FOREIGN KEY (sla_id) REFERENCES sla_definitions(sla_id)
            )
        """)

        # Index for breach queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_breaches_start
            ON sla_breaches(breach_start DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_breaches_unresolved
            ON sla_breaches(resolved, breach_start DESC)
            WHERE resolved = 0
        """)

        # Table 4: Daily SLA Summaries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sla_daily_summaries (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sla_id INTEGER NOT NULL,
                date DATE NOT NULL,
                avg_value REAL NOT NULL,
                min_value REAL NOT NULL,
                max_value REAL NOT NULL,
                target_value REAL NOT NULL,
                compliance_percentage REAL NOT NULL,
                breach_count INTEGER DEFAULT 0,
                total_measurements INTEGER NOT NULL,
                UNIQUE(sla_id, date),
                FOREIGN KEY (sla_id) REFERENCES sla_definitions(sla_id)
            )
        """)

        # Index for daily summary queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_summaries_date
            ON sla_daily_summaries(date DESC)
        """)

        # Table 5: Monthly SLA Reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sla_monthly_reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                sla_id INTEGER NOT NULL,
                avg_compliance REAL NOT NULL,
                total_breaches INTEGER NOT NULL,
                total_breach_duration_seconds INTEGER NOT NULL,
                availability_percentage REAL NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, month, sla_id),
                FOREIGN KEY (sla_id) REFERENCES sla_definitions(sla_id)
            )
        """)

        # Table 6: SLA Notifications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sla_notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sla_id INTEGER NOT NULL,
                breach_id INTEGER,
                notification_type TEXT NOT NULL,
                recipients TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (sla_id) REFERENCES sla_definitions(sla_id),
                FOREIGN KEY (breach_id) REFERENCES sla_breaches(breach_id)
            )
        """)

        self.conn.commit()
        logger.info("SLA database tables created successfully")

    def add_sla_definition(self, name: str, category: str, metric_name: str,
                          target_value: float, unit: str, severity: str,
                          description: str = "", percentile: Optional[int] = None) -> int:
        """
        Add a new SLA definition

        Args:
            name: SLA name (e.g., "API Response Time P95")
            category: Category (availability, performance, reliability, etc.)
            metric_name: Prometheus metric name
            target_value: Target value for compliance
            unit: Unit of measurement (percent, seconds, etc.)
            severity: SLA severity (critical, high, medium, low)
            description: Human-readable description
            percentile: Percentile for performance metrics (50, 95, 99)

        Returns:
            sla_id: ID of created SLA definition
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sla_definitions
            (sla_name, sla_category, description, metric_name, target_value,
             unit, severity, percentile)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, category, description, metric_name, target_value,
              unit, severity, percentile))

        self.conn.commit()
        sla_id = cursor.lastrowid

        logger.info(f"Added SLA definition: {name} (ID: {sla_id})")
        return sla_id

    def record_measurement(self, sla_id: int, actual_value: float,
                          target_value: float, component: Optional[str] = None) -> int:
        """
        Record a single SLA measurement

        Args:
            sla_id: SLA definition ID
            actual_value: Measured value
            target_value: Target value for comparison
            component: Component name (for per-component SLAs)

        Returns:
            measurement_id: ID of recorded measurement
        """
        # Determine compliance
        compliant = self._check_compliance(sla_id, actual_value, target_value)

        # Determine status
        status = self._determine_status(actual_value, target_value)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sla_measurements
            (sla_id, timestamp, actual_value, target_value, compliant, status, component)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sla_id, datetime.utcnow(), actual_value, target_value,
              compliant, status.value, component))

        self.conn.commit()
        measurement_id = cursor.lastrowid

        # Check if this creates a breach
        if not compliant:
            self._check_and_create_breach(sla_id, actual_value, target_value)
        else:
            self._check_and_resolve_breach(sla_id)

        return measurement_id

    def _check_compliance(self, sla_id: int, actual_value: float, target_value: float) -> bool:
        """
        Check if actual value meets SLA target

        Logic depends on SLA category:
        - Availability, reliability, efficiency: actual >= target
        - Performance (latency): actual <= target
        - Error rates: actual <= target
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT sla_category FROM sla_definitions WHERE sla_id = ?", (sla_id,))
        row = cursor.fetchone()
        category = row['sla_category'] if row else ""

        # Categories where higher is better
        if category in ('availability', 'reliability', 'efficiency', 'business'):
            return actual_value >= target_value

        # Categories where lower is better (latency, error rates)
        if category in ('performance',):
            return actual_value <= target_value

        # Default: higher is better
        return actual_value >= target_value

    def _determine_status(self, actual_value: float, target_value: float) -> SLAStatus:
        """
        Determine SLA status based on compliance percentage

        For uptime/availability (higher is better):
        - Excellent: >99.9%
        - Good: 99.0-99.9%
        - Poor: 95.0-99.0%
        - Critical: <95.0%
        """
        # Calculate compliance percentage
        if target_value == 0:
            return SLAStatus.CRITICAL

        compliance_pct = (actual_value / target_value) * 100

        if compliance_pct >= 99.9:
            return SLAStatus.EXCELLENT
        elif compliance_pct >= 99.0:
            return SLAStatus.GOOD
        elif compliance_pct >= 95.0:
            return SLAStatus.POOR
        else:
            return SLAStatus.CRITICAL

    def _check_and_create_breach(self, sla_id: int, actual_value: float, target_value: float):
        """Create a breach record if one doesn't exist"""
        cursor = self.conn.cursor()

        # Check if there's already an open breach
        cursor.execute("""
            SELECT breach_id FROM sla_breaches
            WHERE sla_id = ? AND resolved = 0
            ORDER BY breach_start DESC LIMIT 1
        """, (sla_id,))

        if cursor.fetchone():
            # Breach already exists, just update
            return

        # Get severity from SLA definition
        cursor.execute("SELECT severity FROM sla_definitions WHERE sla_id = ?", (sla_id,))
        row = cursor.fetchone()
        severity = row['severity'] if row else 'high'

        # Create new breach
        cursor.execute("""
            INSERT INTO sla_breaches
            (sla_id, breach_start, target_value, actual_value, severity, resolved)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (sla_id, datetime.utcnow(), target_value, actual_value, severity))

        self.conn.commit()
        breach_id = cursor.lastrowid

        logger.warning(f"SLA breach created: SLA ID {sla_id}, Breach ID {breach_id}")

    def _check_and_resolve_breach(self, sla_id: int):
        """Resolve any open breaches for this SLA"""
        cursor = self.conn.cursor()

        # Find open breaches
        cursor.execute("""
            SELECT breach_id, breach_start FROM sla_breaches
            WHERE sla_id = ? AND resolved = 0
        """, (sla_id,))

        for row in cursor.fetchall():
            breach_id = row['breach_id']
            breach_start = datetime.fromisoformat(row['breach_start'])
            breach_end = datetime.utcnow()
            duration = int((breach_end - breach_start).total_seconds())

            # Update breach as resolved
            cursor.execute("""
                UPDATE sla_breaches
                SET breach_end = ?, duration_seconds = ?, resolved = 1
                WHERE breach_id = ?
            """, (breach_end, duration, breach_id))

            logger.info(f"SLA breach resolved: Breach ID {breach_id}, Duration: {duration}s")

        self.conn.commit()

    def get_current_sla_status(self, hours: int = 24) -> List[Dict]:
        """
        Get current SLA compliance status for all SLAs

        Args:
            hours: Look back period in hours (default: 24)

        Returns:
            List of SLA status dictionaries
        """
        cursor = self.conn.cursor()
        since = datetime.utcnow() - timedelta(hours=hours)

        cursor.execute("""
            SELECT
                d.sla_name,
                d.sla_category,
                d.target_value,
                d.unit,
                d.severity,
                AVG(m.actual_value) as avg_actual,
                MIN(m.actual_value) as min_actual,
                MAX(m.actual_value) as max_actual,
                SUM(CASE WHEN m.compliant THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as compliance_pct,
                COUNT(*) as total_measurements
            FROM sla_definitions d
            LEFT JOIN sla_measurements m ON d.sla_id = m.sla_id
            WHERE m.timestamp >= ? AND d.enabled = 1
            GROUP BY d.sla_id
            ORDER BY d.sla_category, d.sla_name
        """, (since,))

        results = []
        for row in cursor.fetchall():
            results.append({
                'sla_name': row['sla_name'],
                'category': row['sla_category'],
                'target': row['target_value'],
                'unit': row['unit'],
                'severity': row['severity'],
                'avg_actual': row['avg_actual'],
                'min_actual': row['min_actual'],
                'max_actual': row['max_actual'],
                'compliance_pct': row['compliance_pct'],
                'total_measurements': row['total_measurements']
            })

        return results

    def get_active_breaches(self) -> List[SLABreach]:
        """Get all currently active SLA breaches"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                b.breach_id,
                d.sla_name,
                b.breach_start,
                b.breach_end,
                b.duration_seconds,
                b.target_value,
                b.actual_value,
                b.severity,
                b.notified,
                b.resolved
            FROM sla_breaches b
            JOIN sla_definitions d ON b.sla_id = d.sla_id
            WHERE b.resolved = 0
            ORDER BY b.breach_start DESC
        """)

        breaches = []
        for row in cursor.fetchall():
            breaches.append(SLABreach(
                breach_id=row['breach_id'],
                sla_name=row['sla_name'],
                breach_start=datetime.fromisoformat(row['breach_start']),
                breach_end=datetime.fromisoformat(row['breach_end']) if row['breach_end'] else None,
                duration_seconds=row['duration_seconds'],
                target_value=row['target_value'],
                actual_value=row['actual_value'],
                severity=SLASeverity(row['severity']),
                notified=bool(row['notified']),
                resolved=bool(row['resolved'])
            ))

        return breaches

    def generate_daily_summary(self, date: Optional[datetime] = None):
        """
        Generate daily SLA summary for all SLAs

        Args:
            date: Date to summarize (default: yesterday)
        """
        if date is None:
            date = datetime.utcnow().date() - timedelta(days=1)

        cursor = self.conn.cursor()

        # Get all enabled SLAs
        cursor.execute("SELECT sla_id FROM sla_definitions WHERE enabled = 1")
        sla_ids = [row['sla_id'] for row in cursor.fetchall()]

        for sla_id in sla_ids:
            # Calculate daily statistics
            cursor.execute("""
                SELECT
                    AVG(actual_value) as avg_value,
                    MIN(actual_value) as min_value,
                    MAX(actual_value) as max_value,
                    AVG(target_value) as target_value,
                    SUM(CASE WHEN compliant THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as compliance_pct,
                    COUNT(*) as total_measurements
                FROM sla_measurements
                WHERE sla_id = ? AND DATE(timestamp) = ?
            """, (sla_id, date))

            row = cursor.fetchone()
            if row and row['total_measurements'] > 0:
                # Count breaches for this day
                cursor.execute("""
                    SELECT COUNT(*) as breach_count
                    FROM sla_breaches
                    WHERE sla_id = ? AND DATE(breach_start) = ?
                """, (sla_id, date))
                breach_count = cursor.fetchone()['breach_count']

                # Insert summary
                cursor.execute("""
                    INSERT OR REPLACE INTO sla_daily_summaries
                    (sla_id, date, avg_value, min_value, max_value, target_value,
                     compliance_percentage, breach_count, total_measurements)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sla_id, date, row['avg_value'], row['min_value'], row['max_value'],
                      row['target_value'], row['compliance_pct'], breach_count, row['total_measurements']))

        self.conn.commit()
        logger.info(f"Daily summary generated for {date}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("SLA database connection closed")


def init_default_slas(db: SLADatabase):
    """
    Initialize default SLA definitions from sla_thresholds.yml

    Args:
        db: SLADatabase instance
    """
    # Availability SLAs
    db.add_sla_definition(
        name="Platform Uptime",
        category="availability",
        metric_name="up",
        target_value=99.9,
        unit="percent",
        severity="critical",
        description="Overall platform availability"
    )

    db.add_sla_definition(
        name="Agent Worker Uptime",
        category="availability",
        metric_name="insa_worker_health_status",
        target_value=99.9,
        unit="percent",
        severity="critical",
        description="Individual agent worker availability"
    )

    # Performance SLAs
    db.add_sla_definition(
        name="API Response Time P95",
        category="performance",
        metric_name="insa_agent_request_duration_seconds",
        target_value=5.0,
        unit="seconds",
        severity="critical",
        description="95th percentile API response time",
        percentile=95
    )

    db.add_sla_definition(
        name="API Response Time P99",
        category="performance",
        metric_name="insa_agent_request_duration_seconds",
        target_value=15.0,
        unit="seconds",
        severity="critical",
        description="99th percentile API response time",
        percentile=99
    )

    # Reliability SLAs
    db.add_sla_definition(
        name="API Error Rate",
        category="reliability",
        metric_name="insa_agent_requests_total",
        target_value=0.1,
        unit="percent",
        severity="critical",
        description="Percentage of failed API requests"
    )

    db.add_sla_definition(
        name="Retry Success Rate",
        category="reliability",
        metric_name="insa_retry_attempts_total",
        target_value=70.0,
        unit="percent",
        severity="high",
        description="Percentage of successful retry attempts"
    )

    # Efficiency SLAs
    db.add_sla_definition(
        name="Cache Hit Rate",
        category="efficiency",
        metric_name="insa_cache_hits_total",
        target_value=80.0,
        unit="percent",
        severity="high",
        description="Percentage of cache requests served from cache"
    )

    logger.info("Default SLA definitions initialized")


if __name__ == '__main__':
    # Initialize database and add default SLAs
    db = SLADatabase()

    try:
        # Check if we need to initialize default SLAs
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM sla_definitions")
        count = cursor.fetchone()['count']

        if count == 0:
            logger.info("No SLA definitions found. Initializing defaults...")
            init_default_slas(db)
            logger.info("✅ SLA database initialized with default definitions")
        else:
            logger.info(f"✅ SLA database ready ({count} SLA definitions found)")

        # Show current status
        print("\n" + "=" * 60)
        print("SLA DATABASE STATUS")
        print("=" * 60)

        cursor.execute("SELECT COUNT(*) FROM sla_definitions WHERE enabled = 1")
        print(f"Active SLA definitions: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM sla_measurements")
        print(f"Total measurements: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM sla_breaches WHERE resolved = 0")
        print(f"Active breaches: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM sla_daily_summaries")
        print(f"Daily summaries: {cursor.fetchone()[0]}")

        print("=" * 60)

    finally:
        db.close()

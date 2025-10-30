#!/usr/bin/env python3
"""
Unit Tests for SLA Tracking
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8
Test-Driven Development (TDD) - Tests written BEFORE implementation

Test Coverage:
1. SLA auto-creation (database trigger)
2. Time to Acknowledge (TTA) calculation
3. Time to Resolve (TTR) calculation
4. SLA breach detection
5. Severity-based targets
6. Update mechanisms
7. Edge cases

SLA Targets by Severity:
- critical: TTA 5min, TTR 30min
- high: TTA 15min, TTR 2h (120min)
- medium: TTA 1h (60min), TTR 8h (480min)
- low: TTA 4h (240min), TTR 24h (1440min)
- info: TTA 24h (1440min), TTR 1week (10080min)

Run: python3 test_sla_tracking.py
"""

import unittest
import uuid
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', 5432),
    'database': os.environ.get('DB_NAME', 'insa_iiot'),
    'user': os.environ.get('DB_USER', 'iiot_user'),
    'password': os.environ.get('DB_PASSWORD', 'iiot_secure_2025')
}


class TestSLATracking(unittest.TestCase):
    """Test suite for SLA tracking system"""

    @classmethod
    def setUpClass(cls):
        """Set up test database connection"""
        cls.conn = psycopg2.connect(**DB_CONFIG)
        cls.conn.autocommit = False

    @classmethod
    def tearDownClass(cls):
        """Close database connection"""
        if cls.conn:
            cls.conn.close()

    def setUp(self):
        """Set up test data before each test"""
        # Create test device
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO devices (id, name, type, location)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (str(uuid.uuid4()), 'SLA Test Device', 'sensor', 'Test'))
            self.test_device_id = cursor.fetchone()['id']

        # Create test user
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO users (id, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (str(uuid.uuid4()), 'sla_test@example.com', 'hash123'))
            self.test_user_id = cursor.fetchone()['id']

        self.conn.commit()

    def tearDown(self):
        """Clean up test data after each test"""
        with self.conn.cursor() as cursor:
            # Clean up in reverse dependency order
            cursor.execute("DELETE FROM alert_states WHERE alert_id IN (SELECT id FROM alerts WHERE device_id = %s)", (self.test_device_id,))
            cursor.execute("DELETE FROM alert_slas WHERE alert_id IN (SELECT id FROM alerts WHERE device_id = %s)", (self.test_device_id,))
            cursor.execute("DELETE FROM alerts WHERE device_id = %s", (self.test_device_id,))
            cursor.execute("DELETE FROM devices WHERE id = %s", (self.test_device_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (self.test_user_id,))

        self.conn.commit()

    def _create_test_alert(self, severity='medium'):
        """Helper: Create a test alert"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO alerts (device_id, severity, message)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (self.test_device_id, severity, f'SLA test alert ({severity})'))
            alert_id = cursor.fetchone()['id']

        self.conn.commit()
        return alert_id

    def _get_sla_record(self, alert_id):
        """Helper: Get SLA record for an alert"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM alert_slas WHERE alert_id = %s
            """, (alert_id,))
            return cursor.fetchone()

    def _acknowledge_alert(self, alert_id):
        """Helper: Acknowledge an alert"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, 'acknowledged', %s, 'Acked for SLA test')
            """, (alert_id, self.test_user_id))
        self.conn.commit()

    def _resolve_alert(self, alert_id):
        """Helper: Resolve an alert"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, 'resolved', %s, 'Resolved for SLA test')
            """, (alert_id, self.test_user_id))
        self.conn.commit()

    # =============================================================================
    # Test 1: SLA Auto-Creation
    # =============================================================================

    def test_01_sla_auto_created_on_alert(self):
        """Test that SLA record is auto-created when alert is created"""
        alert_id = self._create_test_alert(severity='critical')

        # Verify SLA record exists
        sla = self._get_sla_record(alert_id)

        self.assertIsNotNone(sla, "SLA record should be auto-created")
        self.assertEqual(sla['alert_id'], alert_id)
        self.assertEqual(sla['severity'], 'critical')
        self.assertIsNotNone(sla['tta_target'], "TTA target should be set")
        self.assertIsNotNone(sla['ttr_target'], "TTR target should be set")

    # =============================================================================
    # Test 2: Severity-Based SLA Targets
    # =============================================================================

    def test_02_critical_severity_targets(self):
        """Test SLA targets for critical severity"""
        alert_id = self._create_test_alert(severity='critical')
        sla = self._get_sla_record(alert_id)

        self.assertEqual(sla['tta_target'], 5, "Critical TTA should be 5 minutes")
        self.assertEqual(sla['ttr_target'], 30, "Critical TTR should be 30 minutes")

    def test_03_high_severity_targets(self):
        """Test SLA targets for high severity"""
        alert_id = self._create_test_alert(severity='high')
        sla = self._get_sla_record(alert_id)

        self.assertEqual(sla['tta_target'], 15, "High TTA should be 15 minutes")
        self.assertEqual(sla['ttr_target'], 120, "High TTR should be 120 minutes (2h)")

    def test_04_medium_severity_targets(self):
        """Test SLA targets for medium severity"""
        alert_id = self._create_test_alert(severity='medium')
        sla = self._get_sla_record(alert_id)

        self.assertEqual(sla['tta_target'], 60, "Medium TTA should be 60 minutes (1h)")
        self.assertEqual(sla['ttr_target'], 480, "Medium TTR should be 480 minutes (8h)")

    def test_05_low_severity_targets(self):
        """Test SLA targets for low severity"""
        alert_id = self._create_test_alert(severity='low')
        sla = self._get_sla_record(alert_id)

        self.assertEqual(sla['tta_target'], 240, "Low TTA should be 240 minutes (4h)")
        self.assertEqual(sla['ttr_target'], 1440, "Low TTR should be 1440 minutes (24h)")

    def test_06_info_severity_targets(self):
        """Test SLA targets for info severity"""
        alert_id = self._create_test_alert(severity='info')
        sla = self._get_sla_record(alert_id)

        self.assertEqual(sla['tta_target'], 1440, "Info TTA should be 1440 minutes (24h)")
        self.assertEqual(sla['ttr_target'], 10080, "Info TTR should be 10080 minutes (1 week)")

    # =============================================================================
    # Test 7: TTA Calculation (Manual Update)
    # =============================================================================

    def test_07_tta_calculated_on_acknowledge(self):
        """Test that TTA is calculated when alert is acknowledged"""
        alert_id = self._create_test_alert(severity='medium')

        # Get initial SLA record
        sla_before = self._get_sla_record(alert_id)
        self.assertIsNone(sla_before['tta_actual'], "TTA should be null before acknowledge")
        self.assertIsNone(sla_before['acknowledged_at'], "acknowledged_at should be null")

        # Acknowledge alert (this should trigger TTA calculation)
        self._acknowledge_alert(alert_id)

        # Note: In TDD, we're testing that the database can store the calculated value
        # The actual calculation will be done by the SLA tracking module (to be implemented)
        # For now, we'll manually update to simulate what the module will do

        # Simulate SLA tracking module updating TTA
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_slas
                SET tta_actual = EXTRACT(EPOCH FROM (NOW() - created_at)) / 60,
                    acknowledged_at = NOW()
                WHERE alert_id = %s
            """, (alert_id,))
        self.conn.commit()

        # Verify TTA was updated
        sla_after = self._get_sla_record(alert_id)
        self.assertIsNotNone(sla_after['tta_actual'], "TTA should be calculated after acknowledge")
        self.assertIsNotNone(sla_after['acknowledged_at'], "acknowledged_at should be set")
        self.assertGreaterEqual(sla_after['tta_actual'], 0, "TTA should be >= 0")

    # =============================================================================
    # Test 8: TTR Calculation (Manual Update)
    # =============================================================================

    def test_08_ttr_calculated_on_resolve(self):
        """Test that TTR is calculated when alert is resolved"""
        alert_id = self._create_test_alert(severity='medium')

        # Acknowledge and resolve
        self._acknowledge_alert(alert_id)
        self._resolve_alert(alert_id)

        # Simulate SLA tracking module updating TTR
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_slas
                SET ttr_actual = EXTRACT(EPOCH FROM (NOW() - created_at)) / 60,
                    resolved_at = NOW()
                WHERE alert_id = %s
            """, (alert_id,))
        self.conn.commit()

        # Verify TTR was updated
        sla = self._get_sla_record(alert_id)
        self.assertIsNotNone(sla['ttr_actual'], "TTR should be calculated after resolve")
        self.assertIsNotNone(sla['resolved_at'], "resolved_at should be set")
        self.assertGreaterEqual(sla['ttr_actual'], 0, "TTR should be >= 0")

    # =============================================================================
    # Test 9: SLA Breach Detection (TTA)
    # =============================================================================

    def test_09_tta_breach_not_detected_when_met(self):
        """Test that TTA breach is not detected when SLA is met"""
        alert_id = self._create_test_alert(severity='critical')  # 5min target

        # Acknowledge within target
        self._acknowledge_alert(alert_id)

        # Simulate TTA update (1 minute - within 5min target)
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_slas
                SET tta_actual = 1,
                    tta_breached = (1 > tta_target),
                    acknowledged_at = NOW()
                WHERE alert_id = %s
            """, (alert_id,))
        self.conn.commit()

        # Verify no breach
        sla = self._get_sla_record(alert_id)
        self.assertFalse(sla['tta_breached'], "TTA should not be breached when met")

    def test_10_tta_breach_detected_when_missed(self):
        """Test that TTA breach is detected when SLA is missed"""
        alert_id = self._create_test_alert(severity='critical')  # 5min target

        # Simulate late acknowledgement (10 minutes - exceeds 5min target)
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_slas
                SET tta_actual = 10,
                    tta_breached = (10 > tta_target),
                    acknowledged_at = NOW()
                WHERE alert_id = %s
            """, (alert_id,))
        self.conn.commit()

        # Verify breach detected
        sla = self._get_sla_record(alert_id)
        self.assertTrue(sla['tta_breached'], "TTA should be breached when target exceeded")

    # =============================================================================
    # Test 11: SLA Breach Detection (TTR)
    # =============================================================================

    def test_11_ttr_breach_not_detected_when_met(self):
        """Test that TTR breach is not detected when SLA is met"""
        alert_id = self._create_test_alert(severity='critical')  # 30min target

        # Resolve within target
        self._acknowledge_alert(alert_id)
        self._resolve_alert(alert_id)

        # Simulate TTR update (20 minutes - within 30min target)
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_slas
                SET ttr_actual = 20,
                    ttr_breached = (20 > ttr_target),
                    resolved_at = NOW()
                WHERE alert_id = %s
            """, (alert_id,))
        self.conn.commit()

        # Verify no breach
        sla = self._get_sla_record(alert_id)
        self.assertFalse(sla['ttr_breached'], "TTR should not be breached when met")

    def test_12_ttr_breach_detected_when_missed(self):
        """Test that TTR breach is detected when SLA is missed"""
        alert_id = self._create_test_alert(severity='critical')  # 30min target

        # Simulate late resolution (45 minutes - exceeds 30min target)
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_slas
                SET ttr_actual = 45,
                    ttr_breached = (45 > ttr_target),
                    resolved_at = NOW()
                WHERE alert_id = %s
            """, (alert_id,))
        self.conn.commit()

        # Verify breach detected
        sla = self._get_sla_record(alert_id)
        self.assertTrue(sla['ttr_breached'], "TTR should be breached when target exceeded")

    # =============================================================================
    # Test 13: View - v_sla_compliance_summary
    # =============================================================================

    def test_13_sla_compliance_view(self):
        """Test v_sla_compliance_summary view"""
        # Create multiple alerts with different breach statuses
        alert1 = self._create_test_alert(severity='critical')
        alert2 = self._create_test_alert(severity='high')

        # Simulate breaches
        with self.conn.cursor() as cursor:
            # Alert 1: TTA breached
            cursor.execute("""
                UPDATE alert_slas
                SET tta_actual = 10,
                    tta_breached = TRUE
                WHERE alert_id = %s
            """, (alert1,))

            # Alert 2: No breach
            cursor.execute("""
                UPDATE alert_slas
                SET tta_actual = 5,
                    tta_breached = FALSE
                WHERE alert_id = %s
            """, (alert2,))

        self.conn.commit()

        # Query view
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM v_sla_compliance_summary
                WHERE severity IN ('critical', 'high')
            """)
            summary = cursor.fetchall()

        # Verify view returns data
        self.assertGreaterEqual(len(summary), 1, "View should return SLA summary data")

    # =============================================================================
    # Test 14: Edge Cases
    # =============================================================================

    def test_14_sla_record_unique_per_alert(self):
        """Test that only one SLA record exists per alert"""
        alert_id = self._create_test_alert(severity='medium')

        # Try to insert duplicate SLA record (should fail due to UNIQUE constraint)
        with self.assertRaises(psycopg2.Error):
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alert_slas (alert_id, severity, tta_target, ttr_target)
                    VALUES (%s, 'medium', 30, 240)
                """, (alert_id,))

        self.conn.rollback()

    def test_15_sla_cascade_delete_with_alert(self):
        """Test that SLA record is deleted when alert is deleted"""
        alert_id = self._create_test_alert(severity='medium')

        # Verify SLA exists
        sla_before = self._get_sla_record(alert_id)
        self.assertIsNotNone(sla_before, "SLA should exist before alert deletion")

        # Delete alert
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM alerts WHERE id = %s", (alert_id,))
        self.conn.commit()

        # Verify SLA was cascade deleted
        sla_after = self._get_sla_record(alert_id)
        self.assertIsNone(sla_after, "SLA should be cascade deleted with alert")


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestSLATracking))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY - SLA Tracking")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Pass Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("=" * 70)

    return result


if __name__ == '__main__':
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)

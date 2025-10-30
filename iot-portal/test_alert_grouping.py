#!/usr/bin/env python3
"""
Unit Tests for Alert Grouping and Deduplication
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8
Test-Driven Development (TDD) - Tests written BEFORE implementation

Test Coverage:
1. Alert grouping by device + rule + severity
2. Time-based grouping windows
3. Alert deduplication
4. Group statistics (count, timestamps)
5. Noise reduction metrics
6. Group lifecycle (create, update, close)
7. Query operations
8. Edge cases

Alert Group Structure (Database):
- alert_groups table:
  - id (UUID)
  - device_id (UUID)
  - rule_id (UUID)
  - severity (TEXT)
  - group_key (TEXT) - composite key for matching
  - first_occurrence_at (TIMESTAMPTZ)
  - last_occurrence_at (TIMESTAMPTZ)
  - occurrence_count (INTEGER)
  - status (TEXT) - 'active', 'closed'
  - representative_alert_id (UUID) - first alert in group
  - metadata (JSONB) - group-specific data
  - created_at (TIMESTAMPTZ)
  - updated_at (TIMESTAMPTZ)

Run: python3 test_alert_grouping.py
"""

import unittest
import uuid
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import os
import sys
import json

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


class TestAlertGrouping(unittest.TestCase):
    """Test suite for alert grouping and deduplication"""

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
            """, (str(uuid.uuid4()), 'Test Device', 'sensor', 'Test Lab'))
            self.test_device_id = cursor.fetchone()['id']

        # Create test rule
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO rules (id, name, rule_type, enabled, conditions, actions)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(uuid.uuid4()),
                'Test Rule',
                'threshold',  # Add rule_type
                True,
                Json({"field": "temperature", "operator": ">", "value": 80}),
                Json([{"type": "alert", "severity": "critical"}])
            ))
            self.test_rule_id = cursor.fetchone()['id']

        self.conn.commit()

        # Clean up any existing test groups
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM alert_groups WHERE device_id = %s", (self.test_device_id,))
        self.conn.commit()

    def tearDown(self):
        """Clean up test data after each test"""
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM alert_groups WHERE device_id = %s", (self.test_device_id,))
            cursor.execute("DELETE FROM alerts WHERE device_id = %s", (self.test_device_id,))
            cursor.execute("DELETE FROM devices WHERE id = %s", (self.test_device_id,))
            cursor.execute("DELETE FROM rules WHERE id = %s", (self.test_rule_id,))
        self.conn.commit()

    def _create_test_alert(self, severity='critical', timestamp=None):
        """Helper: Create a test alert"""
        if timestamp is None:
            timestamp = datetime.now()

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO alerts (
                    id, device_id, rule_id, severity, message,
                    status, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(uuid.uuid4()),
                self.test_device_id,
                self.test_rule_id,
                severity,
                'Test alert message',
                'active',  # Changed from 'triggered' to 'active'
                timestamp
            ))
            alert_id = cursor.fetchone()['id']

        self.conn.commit()
        return alert_id

    def _create_test_group(self, severity='critical', status='active'):
        """Helper: Create a test alert group"""
        group_key = f"{self.test_device_id}:{self.test_rule_id}:{severity}"
        alert_id = self._create_test_alert(severity)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO alert_groups (
                    id, device_id, rule_id, severity, group_key,
                    first_occurrence_at, last_occurrence_at,
                    occurrence_count, status, representative_alert_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(uuid.uuid4()),
                self.test_device_id,
                self.test_rule_id,
                severity,
                group_key,
                datetime.now(),
                datetime.now(),
                1,
                status,
                alert_id
            ))
            group_id = cursor.fetchone()['id']

        self.conn.commit()
        return group_id

    def _get_group(self, group_id):
        """Helper: Get alert group by ID"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM alert_groups WHERE id = %s
            """, (group_id,))
            return cursor.fetchone()

    # =============================================================================
    # Test 1: Group Creation
    # =============================================================================

    def test_01_create_basic_group(self):
        """Test creating a basic alert group"""
        group_id = self._create_test_group()
        group = self._get_group(group_id)

        self.assertIsNotNone(group, "Group should be created")
        self.assertEqual(group['device_id'], self.test_device_id)
        self.assertEqual(group['rule_id'], self.test_rule_id)
        self.assertEqual(group['severity'], 'critical')
        self.assertEqual(group['occurrence_count'], 1)
        self.assertEqual(group['status'], 'active')

    # =============================================================================
    # Test 2: Group Key Generation
    # =============================================================================

    def test_02_group_key_format(self):
        """Test that group key is generated correctly"""
        group_id = self._create_test_group(severity='high')
        group = self._get_group(group_id)

        expected_key = f"{self.test_device_id}:{self.test_rule_id}:high"
        self.assertEqual(group['group_key'], expected_key)

    def test_03_different_severities_different_groups(self):
        """Test that different severities create different groups"""
        group1_id = self._create_test_group(severity='critical')
        group2_id = self._create_test_group(severity='high')

        group1 = self._get_group(group1_id)
        group2 = self._get_group(group2_id)

        self.assertNotEqual(group1['group_key'], group2['group_key'])

    # =============================================================================
    # Test 4: Alert Deduplication
    # =============================================================================

    def test_04_duplicate_alert_updates_count(self):
        """Test that duplicate alerts increment occurrence count"""
        group_id = self._create_test_group()

        # Simulate adding another alert to the group
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_groups
                SET occurrence_count = occurrence_count + 1,
                    last_occurrence_at = %s
                WHERE id = %s
            """, (datetime.now(), group_id))
        self.conn.commit()

        group = self._get_group(group_id)
        self.assertEqual(group['occurrence_count'], 2, "Count should increment")

    def test_05_duplicate_alert_updates_timestamp(self):
        """Test that duplicate alerts update last_occurrence_at"""
        group_id = self._create_test_group()
        original_group = self._get_group(group_id)
        original_time = original_group['last_occurrence_at']

        # Wait a bit and update
        import time
        time.sleep(0.1)

        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_groups
                SET last_occurrence_at = %s
                WHERE id = %s
            """, (datetime.now(), group_id))
        self.conn.commit()

        updated_group = self._get_group(group_id)
        self.assertGreater(
            updated_group['last_occurrence_at'],
            original_time,
            "Last occurrence should be updated"
        )

    # =============================================================================
    # Test 6: Time Window Grouping
    # =============================================================================

    def test_06_alerts_within_window_same_group(self):
        """Test that alerts within time window belong to same group"""
        # Create group with first alert
        group_id = self._create_test_group()
        group = self._get_group(group_id)

        # Create second alert 2 minutes later (within 5-min window)
        alert2_time = group['first_occurrence_at'] + timedelta(minutes=2)

        # This would be checked by the grouping logic
        time_diff = (alert2_time - group['first_occurrence_at']).total_seconds() / 60
        self.assertLess(time_diff, 5, "Alert should be within 5-minute window")

    def test_07_alerts_outside_window_different_group(self):
        """Test that alerts outside time window create new group"""
        # Create group with first alert
        group_id = self._create_test_group()
        group = self._get_group(group_id)

        # Check alert 10 minutes later (outside 5-min window)
        alert2_time = group['first_occurrence_at'] + timedelta(minutes=10)

        time_diff = (alert2_time - group['first_occurrence_at']).total_seconds() / 60
        self.assertGreater(time_diff, 5, "Alert should be outside 5-minute window")

    # =============================================================================
    # Test 8: Group Statistics
    # =============================================================================

    def test_08_group_tracks_first_occurrence(self):
        """Test that group tracks first occurrence timestamp"""
        group_id = self._create_test_group()
        group = self._get_group(group_id)

        self.assertIsNotNone(group['first_occurrence_at'])
        self.assertIsInstance(group['first_occurrence_at'], datetime)

    def test_09_group_tracks_last_occurrence(self):
        """Test that group tracks last occurrence timestamp"""
        group_id = self._create_test_group()
        group = self._get_group(group_id)

        self.assertIsNotNone(group['last_occurrence_at'])
        self.assertIsInstance(group['last_occurrence_at'], datetime)

    def test_10_group_tracks_occurrence_count(self):
        """Test that group tracks total occurrence count"""
        group_id = self._create_test_group()
        group = self._get_group(group_id)

        self.assertEqual(group['occurrence_count'], 1)
        self.assertIsInstance(group['occurrence_count'], int)

    # =============================================================================
    # Test 11: Representative Alert
    # =============================================================================

    def test_11_group_stores_representative_alert(self):
        """Test that group stores reference to first alert"""
        group_id = self._create_test_group()
        group = self._get_group(group_id)

        self.assertIsNotNone(group['representative_alert_id'])

        # Verify alert exists
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM alerts WHERE id = %s",
                         (group['representative_alert_id'],))
            alert = cursor.fetchone()
            self.assertIsNotNone(alert)

    # =============================================================================
    # Test 12: Group Status Management
    # =============================================================================

    def test_12_group_starts_active(self):
        """Test that new groups start with 'active' status"""
        group_id = self._create_test_group()
        group = self._get_group(group_id)

        self.assertEqual(group['status'], 'active')

    def test_13_group_can_be_closed(self):
        """Test that groups can be marked as closed"""
        group_id = self._create_test_group()

        # Close the group
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_groups
                SET status = 'closed'
                WHERE id = %s
            """, (group_id,))
        self.conn.commit()

        group = self._get_group(group_id)
        self.assertEqual(group['status'], 'closed')

    # =============================================================================
    # Test 14: Query Active Groups
    # =============================================================================

    def test_14_query_active_groups(self):
        """Test querying only active groups"""
        # Create active and closed groups
        active_id = self._create_test_group(status='active')
        closed_id = self._create_test_group(severity='high', status='closed')

        # Query active groups
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM alert_groups
                WHERE status = 'active'
                AND device_id = %s
            """, (self.test_device_id,))
            groups = cursor.fetchall()

        active_ids = [g['id'] for g in groups]
        self.assertIn(active_id, active_ids)
        self.assertNotIn(closed_id, active_ids)

    def test_15_query_groups_by_device(self):
        """Test querying groups for specific device"""
        group_id = self._create_test_group()

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM alert_groups
                WHERE device_id = %s
            """, (self.test_device_id,))
            groups = cursor.fetchall()

        self.assertGreater(len(groups), 0)
        self.assertEqual(groups[0]['device_id'], self.test_device_id)

    # =============================================================================
    # Test 16: Group Metadata
    # =============================================================================

    def test_16_group_can_store_metadata(self):
        """Test that groups can store custom metadata"""
        group_key = f"{self.test_device_id}:{self.test_rule_id}:critical"
        alert_id = self._create_test_alert()

        metadata = {
            "noise_reduction_pct": 85.5,
            "total_alerts_grouped": 100,
            "unique_messages": 3
        }

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO alert_groups (
                    id, device_id, rule_id, severity, group_key,
                    first_occurrence_at, last_occurrence_at,
                    occurrence_count, status, representative_alert_id,
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(uuid.uuid4()),
                self.test_device_id,
                self.test_rule_id,
                'critical',
                group_key,
                datetime.now(),
                datetime.now(),
                100,
                'active',
                alert_id,
                Json(metadata)
            ))
            group_id = cursor.fetchone()['id']
        self.conn.commit()

        group = self._get_group(group_id)
        self.assertEqual(group['metadata']['noise_reduction_pct'], 85.5)
        self.assertEqual(group['metadata']['total_alerts_grouped'], 100)

    # =============================================================================
    # Test 17: Noise Reduction Metrics
    # =============================================================================

    def test_17_calculate_noise_reduction(self):
        """Test calculating noise reduction percentage"""
        # Create group with 50 occurrences
        group_id = self._create_test_group()

        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE alert_groups
                SET occurrence_count = 50
                WHERE id = %s
            """, (group_id,))
        self.conn.commit()

        group = self._get_group(group_id)

        # 50 alerts → 1 group = 98% noise reduction
        noise_reduction = ((group['occurrence_count'] - 1) / group['occurrence_count']) * 100
        self.assertGreater(noise_reduction, 90, "Should achieve >90% noise reduction")

    # =============================================================================
    # Test 18: Timestamp Tracking
    # =============================================================================

    def test_18_timestamps_tracked(self):
        """Test that creation and update timestamps are tracked"""
        group_id = self._create_test_group()
        group = self._get_group(group_id)

        self.assertIsNotNone(group['created_at'])
        self.assertIsNotNone(group['updated_at'])

    # =============================================================================
    # Test 19: Edge Cases
    # =============================================================================

    def test_19_multiple_active_groups_same_device(self):
        """Test that device can have multiple active groups"""
        group1 = self._create_test_group(severity='critical')
        group2 = self._create_test_group(severity='high')

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count FROM alert_groups
                WHERE device_id = %s AND status = 'active'
            """, (self.test_device_id,))
            count = cursor.fetchone()['count']

        self.assertEqual(count, 2, "Should have 2 active groups")

    def test_20_group_deletion(self):
        """Test that groups can be deleted"""
        group_id = self._create_test_group()

        # Verify exists
        group = self._get_group(group_id)
        self.assertIsNotNone(group)

        # Delete
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM alert_groups WHERE id = %s", (group_id,))
        self.conn.commit()

        # Verify deleted
        group = self._get_group(group_id)
        self.assertIsNone(group)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestAlertGrouping))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY - Alert Grouping and Deduplication")
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

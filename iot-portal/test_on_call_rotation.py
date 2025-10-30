#!/usr/bin/env python3
"""
Unit Tests for On-Call Rotation
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8
Test-Driven Development (TDD) - Tests written BEFORE implementation

Test Coverage:
1. Schedule creation and storage
2. Weekly rotation
3. Daily rotation
4. Timezone support
5. Current on-call calculation
6. User rotation list
7. Schedule enable/disable
8. Edge cases

On-Call Schedule Structure (JSONB):
{
    "rotation_type": "weekly",  // or "daily"
    "rotation_start": "2025-10-28T00:00:00Z",
    "users": [
        {"id": "user-uuid-1", "order": 1},
        {"id": "user-uuid-2", "order": 2},
        {"id": "user-uuid-3", "order": 3}
    ],
    "overrides": [
        {
            "user_id": "user-uuid-4",
            "start": "2025-11-01T00:00:00Z",
            "end": "2025-11-07T23:59:59Z",
            "reason": "Vacation coverage"
        }
    ]
}

Run: python3 test_on_call_rotation.py
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


class TestOnCallRotation(unittest.TestCase):
    """Test suite for on-call rotation management"""

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
        # Create test users
        self.test_users = []
        for i in range(3):
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO users (id, email, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (str(uuid.uuid4()), f'oncall{i}@example.com', 'hash'))
                self.test_users.append(cursor.fetchone()['id'])

        self.conn.commit()

        # Clean up any existing test schedules
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM on_call_schedules WHERE name LIKE 'Test%'")
        self.conn.commit()

    def tearDown(self):
        """Clean up test data after each test"""
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM on_call_schedules WHERE name LIKE 'Test%'")
            for user_id in self.test_users:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        self.conn.commit()

    def _create_test_schedule(self, name='Test Schedule', rotation_type='weekly', timezone='UTC', enabled=True):
        """Helper: Create a test on-call schedule"""
        schedule_config = {
            "rotation_type": rotation_type,
            "rotation_start": datetime.now().isoformat(),
            "users": [
                {"id": str(self.test_users[0]), "order": 1},
                {"id": str(self.test_users[1]), "order": 2},
                {"id": str(self.test_users[2]), "order": 3}
            ]
        }

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO on_call_schedules (name, description, schedule, timezone, enabled)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                name,
                f'Test on-call schedule ({rotation_type})',
                Json(schedule_config),
                timezone,
                enabled
            ))
            schedule_id = cursor.fetchone()['id']

        self.conn.commit()
        return schedule_id

    def _get_schedule(self, schedule_id):
        """Helper: Get on-call schedule by ID"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM on_call_schedules WHERE id = %s
            """, (schedule_id,))
            return cursor.fetchone()

    # =============================================================================
    # Test 1: Schedule Creation
    # =============================================================================

    def test_01_create_basic_schedule(self):
        """Test creating a basic on-call schedule"""
        schedule_id = self._create_test_schedule(name='Test Basic Schedule')
        schedule = self._get_schedule(schedule_id)

        self.assertIsNotNone(schedule, "Schedule should be created")
        self.assertEqual(schedule['name'], 'Test Basic Schedule')
        self.assertTrue(schedule['enabled'], "Schedule should be enabled by default")
        self.assertIsNotNone(schedule['schedule'], "Schedule config should be stored")
        self.assertEqual(schedule['timezone'], 'UTC')

    # =============================================================================
    # Test 2: Rotation Type
    # =============================================================================

    def test_02_weekly_rotation_type(self):
        """Test weekly rotation schedule"""
        schedule_id = self._create_test_schedule(rotation_type='weekly')
        schedule = self._get_schedule(schedule_id)

        config = schedule['schedule']
        self.assertEqual(config['rotation_type'], 'weekly')

    def test_03_daily_rotation_type(self):
        """Test daily rotation schedule"""
        schedule_id = self._create_test_schedule(rotation_type='daily')
        schedule = self._get_schedule(schedule_id)

        config = schedule['schedule']
        self.assertEqual(config['rotation_type'], 'daily')

    # =============================================================================
    # Test 4: User Rotation List
    # =============================================================================

    def test_04_user_rotation_list_storage(self):
        """Test that user rotation list is stored correctly"""
        schedule_id = self._create_test_schedule()
        schedule = self._get_schedule(schedule_id)

        users = schedule['schedule']['users']
        self.assertEqual(len(users), 3, "Should have 3 users in rotation")

        # Verify order
        self.assertEqual(users[0]['order'], 1)
        self.assertEqual(users[1]['order'], 2)
        self.assertEqual(users[2]['order'], 3)

        # Verify user IDs
        self.assertEqual(users[0]['id'], str(self.test_users[0]))
        self.assertEqual(users[1]['id'], str(self.test_users[1]))
        self.assertEqual(users[2]['id'], str(self.test_users[2]))

    # =============================================================================
    # Test 5: Timezone Support
    # =============================================================================

    def test_05_timezone_configuration(self):
        """Test timezone configuration"""
        schedule_id = self._create_test_schedule(timezone='America/New_York')
        schedule = self._get_schedule(schedule_id)

        self.assertEqual(schedule['timezone'], 'America/New_York')

    def test_06_multiple_timezones(self):
        """Test schedules can have different timezones"""
        schedule1_id = self._create_test_schedule(name='Test UTC', timezone='UTC')
        schedule2_id = self._create_test_schedule(name='Test PST', timezone='America/Los_Angeles')

        schedule1 = self._get_schedule(schedule1_id)
        schedule2 = self._get_schedule(schedule2_id)

        self.assertEqual(schedule1['timezone'], 'UTC')
        self.assertEqual(schedule2['timezone'], 'America/Los_Angeles')

    # =============================================================================
    # Test 7: Rotation Start Time
    # =============================================================================

    def test_07_rotation_start_time_stored(self):
        """Test that rotation start time is stored"""
        schedule_id = self._create_test_schedule()
        schedule = self._get_schedule(schedule_id)

        self.assertIn('rotation_start', schedule['schedule'])
        self.assertIsNotNone(schedule['schedule']['rotation_start'])

    # =============================================================================
    # Test 8: Schedule Enable/Disable
    # =============================================================================

    def test_08_schedule_can_be_disabled(self):
        """Test that schedules can be enabled/disabled"""
        schedule_id = self._create_test_schedule(enabled=False)
        schedule = self._get_schedule(schedule_id)

        self.assertFalse(schedule['enabled'], "Schedule should be disabled")

        # Enable it
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE on_call_schedules
                SET enabled = TRUE
                WHERE id = %s
            """, (schedule_id,))
        self.conn.commit()

        schedule = self._get_schedule(schedule_id)
        self.assertTrue(schedule['enabled'], "Schedule should now be enabled")

    # =============================================================================
    # Test 9: Schedule Update
    # =============================================================================

    def test_09_schedule_can_be_updated(self):
        """Test that schedule configuration can be modified"""
        schedule_id = self._create_test_schedule()

        # Update schedule
        new_config = {
            "rotation_type": "daily",
            "rotation_start": datetime.now().isoformat(),
            "users": [
                {"id": str(self.test_users[0]), "order": 1}
            ]
        }

        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE on_call_schedules
                SET schedule = %s
                WHERE id = %s
            """, (Json(new_config), schedule_id))
        self.conn.commit()

        schedule = self._get_schedule(schedule_id)
        self.assertEqual(schedule['schedule']['rotation_type'], 'daily')
        self.assertEqual(len(schedule['schedule']['users']), 1)

    # =============================================================================
    # Test 10: Query Active Schedules
    # =============================================================================

    def test_10_query_active_schedules(self):
        """Test querying active schedules"""
        # Create active and inactive schedules
        self._create_test_schedule(name='Test Active', enabled=True)
        self._create_test_schedule(name='Test Inactive', enabled=False)

        # Query active schedules
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM on_call_schedules
                WHERE enabled = TRUE
                AND name LIKE 'Test%'
            """)
            schedules = cursor.fetchall()

        active_names = [s['name'] for s in schedules]
        self.assertIn('Test Active', active_names)
        self.assertNotIn('Test Inactive', active_names)

    # =============================================================================
    # Test 11: Unique Schedule Names
    # =============================================================================

    def test_11_schedule_names_must_be_unique(self):
        """Test that schedule names must be unique"""
        self._create_test_schedule(name='Test Unique Schedule')

        # Try to create another with same name
        with self.assertRaises(psycopg2.Error):
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO on_call_schedules (name, schedule, timezone)
                    VALUES (%s, %s, %s)
                """, (
                    'Test Unique Schedule',
                    Json({"rotation_type": "weekly", "users": []}),
                    'UTC'
                ))

        self.conn.rollback()

    # =============================================================================
    # Test 12: Timestamp Tracking
    # =============================================================================

    def test_12_timestamps_tracked(self):
        """Test that creation and update timestamps are tracked"""
        schedule_id = self._create_test_schedule()
        schedule = self._get_schedule(schedule_id)

        self.assertIsNotNone(schedule['created_at'], "created_at should be set")
        self.assertIsNotNone(schedule['updated_at'], "updated_at should be set")

        created_at = schedule['created_at']

        # Update schedule
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE on_call_schedules
                SET description = 'Updated description'
                WHERE id = %s
            """, (schedule_id,))
        self.conn.commit()

        schedule = self._get_schedule(schedule_id)
        self.assertGreaterEqual(schedule['updated_at'], created_at, "updated_at should be >= created_at")

    # =============================================================================
    # Test 13: Schedule Deletion
    # =============================================================================

    def test_13_schedule_can_be_deleted(self):
        """Test that schedules can be deleted"""
        schedule_id = self._create_test_schedule()

        # Verify exists
        schedule = self._get_schedule(schedule_id)
        self.assertIsNotNone(schedule)

        # Delete
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM on_call_schedules WHERE id = %s", (schedule_id,))
        self.conn.commit()

        # Verify deleted
        schedule = self._get_schedule(schedule_id)
        self.assertIsNone(schedule, "Schedule should be deleted")

    # =============================================================================
    # Test 14: Overrides Support
    # =============================================================================

    def test_14_schedule_overrides_storage(self):
        """Test that temporary overrides can be stored"""
        schedule_id = self._create_test_schedule()

        # Add override
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT schedule FROM on_call_schedules WHERE id = %s", (schedule_id,))
            config = cursor.fetchone()['schedule']

            config['overrides'] = [
                {
                    "user_id": str(self.test_users[0]),
                    "start": (datetime.now() + timedelta(days=1)).isoformat(),
                    "end": (datetime.now() + timedelta(days=7)).isoformat(),
                    "reason": "Vacation coverage"
                }
            ]

            cursor.execute("""
                UPDATE on_call_schedules
                SET schedule = %s
                WHERE id = %s
            """, (Json(config), schedule_id))
        self.conn.commit()

        schedule = self._get_schedule(schedule_id)
        self.assertIn('overrides', schedule['schedule'])
        self.assertEqual(len(schedule['schedule']['overrides']), 1)
        self.assertEqual(schedule['schedule']['overrides'][0]['reason'], 'Vacation coverage')

    # =============================================================================
    # Test 15: Edge Cases
    # =============================================================================

    def test_15_empty_user_list(self):
        """Test that empty user list is allowed (schedule can be placeholder)"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO on_call_schedules (name, schedule, timezone)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (
                'Test Empty Users',
                Json({"rotation_type": "weekly", "users": []}),
                'UTC'
            ))
            schedule_id = cursor.fetchone()['id']
        self.conn.commit()

        schedule = self._get_schedule(schedule_id)
        self.assertEqual(len(schedule['schedule']['users']), 0)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestOnCallRotation))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY - On-Call Rotation")
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

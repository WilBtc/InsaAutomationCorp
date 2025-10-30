#!/usr/bin/env python3
"""
Unit Tests for Alert State Machine
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8
Test-Driven Development (TDD) - Tests written BEFORE implementation

Test Coverage:
1. State transitions (valid and invalid)
2. State history tracking
3. Notes attachment
4. User tracking
5. Timestamp validation
6. Edge cases and error handling

Run: python3 test_alert_state_machine.py
"""

import unittest
import uuid
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys

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


class TestAlertStateMachine(unittest.TestCase):
    """Test suite for alert state machine"""

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
            """, (str(uuid.uuid4()), 'Test Device', 'sensor', 'Test Location'))
            self.test_device_id = cursor.fetchone()['id']

        # Create test user (for RBAC integration)
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO users (id, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (str(uuid.uuid4()), 'test@example.com', 'hash123'))
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
            """, (self.test_device_id, severity, 'Test alert message'))
            alert_id = cursor.fetchone()['id']

        self.conn.commit()
        return alert_id

    def _get_alert_states(self, alert_id):
        """Helper: Get all states for an alert"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT state, changed_by, notes, changed_at
                FROM alert_states
                WHERE alert_id = %s
                ORDER BY changed_at ASC
            """, (alert_id,))
            return cursor.fetchall()

    def _get_current_state(self, alert_id):
        """Helper: Get current state of an alert"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT state, changed_by, notes, changed_at
                FROM alert_states
                WHERE alert_id = %s
                ORDER BY changed_at DESC
                LIMIT 1
            """, (alert_id,))
            return cursor.fetchone()

    # =============================================================================
    # Test 1: Initial State Creation
    # =============================================================================

    def test_01_initial_state_created(self):
        """Test that 'new' state is auto-created when alert is created"""
        # Create alert
        alert_id = self._create_test_alert()

        # Verify initial state
        states = self._get_alert_states(alert_id)

        self.assertEqual(len(states), 1, "Should have exactly 1 initial state")
        self.assertEqual(states[0]['state'], 'new', "Initial state should be 'new'")
        self.assertIsNone(states[0]['changed_by'], "Initial state should have no user (system-created)")
        self.assertIn('Alert created by system', states[0]['notes'], "Initial state should have system note")

    # =============================================================================
    # Test 2: Valid State Transition (new → acknowledged)
    # =============================================================================

    def test_02_transition_new_to_acknowledged(self):
        """Test valid transition from 'new' to 'acknowledged'"""
        # This will be implemented by alert_state_machine.py
        # For now, we'll test the database supports it
        alert_id = self._create_test_alert()

        # Manually insert acknowledged state (simulating state machine)
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, 'Investigating temperature spike'))

        self.conn.commit()

        # Verify state history
        states = self._get_alert_states(alert_id)

        self.assertEqual(len(states), 2, "Should have 2 states (new, acknowledged)")
        self.assertEqual(states[1]['state'], 'acknowledged')
        self.assertEqual(states[1]['changed_by'], self.test_user_id)
        self.assertEqual(states[1]['notes'], 'Investigating temperature spike')

    # =============================================================================
    # Test 3: Valid State Transition (new → investigating)
    # =============================================================================

    def test_03_transition_new_to_investigating(self):
        """Test valid transition from 'new' to 'investigating' (skip acknowledge)"""
        alert_id = self._create_test_alert()

        # Skip acknowledged, go straight to investigating
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'investigating', self.test_user_id, 'Root cause analysis'))

        self.conn.commit()

        # Verify transition
        current_state = self._get_current_state(alert_id)

        self.assertEqual(current_state['state'], 'investigating')
        self.assertEqual(current_state['notes'], 'Root cause analysis')

    # =============================================================================
    # Test 4: Valid State Transition (acknowledged → investigating)
    # =============================================================================

    def test_04_transition_acknowledged_to_investigating(self):
        """Test valid transition from 'acknowledged' to 'investigating'"""
        alert_id = self._create_test_alert()

        # new → acknowledged
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, 'Acked'))

        # acknowledged → investigating
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'investigating', self.test_user_id, 'Starting investigation'))

        self.conn.commit()

        # Verify state progression
        states = self._get_alert_states(alert_id)

        self.assertEqual(len(states), 3)
        self.assertEqual([s['state'] for s in states], ['new', 'acknowledged', 'investigating'])

    # =============================================================================
    # Test 5: Valid State Transition (acknowledged → resolved)
    # =============================================================================

    def test_05_transition_acknowledged_to_resolved(self):
        """Test valid transition from 'acknowledged' to 'resolved' (quick fix)"""
        alert_id = self._create_test_alert()

        # new → acknowledged
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, 'Acked'))
        self.conn.commit()

        # acknowledged → resolved (skip investigating)
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'resolved', self.test_user_id, 'Quick fix applied'))
        self.conn.commit()

        # Verify final state
        current_state = self._get_current_state(alert_id)

        self.assertEqual(current_state['state'], 'resolved')
        self.assertEqual(current_state['notes'], 'Quick fix applied')

    # =============================================================================
    # Test 6: Valid State Transition (investigating → resolved)
    # =============================================================================

    def test_06_transition_investigating_to_resolved(self):
        """Test valid transition from 'investigating' to 'resolved'"""
        alert_id = self._create_test_alert()

        # new → investigating
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'investigating', self.test_user_id, 'Investigating'))

        # investigating → resolved
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'resolved', self.test_user_id, 'Issue fixed'))

        self.conn.commit()

        # Verify complete lifecycle
        states = self._get_alert_states(alert_id)

        self.assertEqual(len(states), 3)
        self.assertEqual([s['state'] for s in states], ['new', 'investigating', 'resolved'])

    # =============================================================================
    # Test 7: State History Recording
    # =============================================================================

    def test_07_state_history_complete(self):
        """Test that complete state history is recorded"""
        alert_id = self._create_test_alert()

        # Complete lifecycle: new → acknowledged → investigating → resolved
        transitions = [
            ('acknowledged', 'Acknowledged by operator'),
            ('investigating', 'Root cause: cooling failure'),
            ('resolved', 'Cooling system repaired')
        ]

        for state, notes in transitions:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alert_states (alert_id, state, changed_by, notes)
                    VALUES (%s, %s, %s, %s)
                """, (alert_id, state, self.test_user_id, notes))

        self.conn.commit()

        # Verify complete history
        states = self._get_alert_states(alert_id)

        self.assertEqual(len(states), 4, "Should have 4 states (new + 3 transitions)")

        expected_states = ['new', 'acknowledged', 'investigating', 'resolved']
        actual_states = [s['state'] for s in states]
        self.assertEqual(actual_states, expected_states, "State sequence should match")

        # Verify timestamps are in order
        timestamps = [s['changed_at'] for s in states]
        self.assertEqual(timestamps, sorted(timestamps), "Timestamps should be chronologically ordered")

    # =============================================================================
    # Test 8: Notes Attachment
    # =============================================================================

    def test_08_notes_attachment(self):
        """Test that notes are properly attached to state transitions"""
        alert_id = self._create_test_alert()

        # Add state with detailed notes
        detailed_notes = """
        Investigation findings:
        1. Cooling fan motor failed
        2. Backup cooling inactive
        3. Temperature reached 85°C (critical threshold: 75°C)
        Resolution: Replaced fan motor, tested backup system
        """

        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'resolved', self.test_user_id, detailed_notes))

        self.conn.commit()

        # Verify notes
        current_state = self._get_current_state(alert_id)

        self.assertIn('Cooling fan motor failed', current_state['notes'])
        self.assertIn('Replaced fan motor', current_state['notes'])

    # =============================================================================
    # Test 9: User Tracking
    # =============================================================================

    def test_09_user_tracking(self):
        """Test that user who made state change is tracked"""
        alert_id = self._create_test_alert()

        # Create second test user
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO users (id, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (str(uuid.uuid4()), 'test2@example.com', 'hash456'))
            user2_id = cursor.fetchone()['id']

        self.conn.commit()

        # User 1 acknowledges
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, 'User 1 acked'))

        # User 2 resolves
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'resolved', user2_id, 'User 2 resolved'))

        self.conn.commit()

        # Verify different users tracked
        states = self._get_alert_states(alert_id)

        self.assertEqual(states[1]['changed_by'], self.test_user_id, "User 1 should be tracked for acknowledge")
        self.assertEqual(states[2]['changed_by'], user2_id, "User 2 should be tracked for resolve")

        # Cleanup
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user2_id,))
        self.conn.commit()

    # =============================================================================
    # Test 10: Timestamp Validation
    # =============================================================================

    def test_10_timestamp_chronological(self):
        """Test that timestamps are chronologically ordered"""
        alert_id = self._create_test_alert()

        # Add multiple state transitions
        for state in ['acknowledged', 'investigating', 'resolved']:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alert_states (alert_id, state, changed_by, notes)
                    VALUES (%s, %s, %s, %s)
                """, (alert_id, state, self.test_user_id, f'{state} state'))

            self.conn.commit()

        # Verify timestamps
        states = self._get_alert_states(alert_id)

        for i in range(len(states) - 1):
            self.assertLess(
                states[i]['changed_at'],
                states[i + 1]['changed_at'],
                f"State {i} timestamp should be before state {i+1}"
            )

    # =============================================================================
    # Test 11: Current State Retrieval
    # =============================================================================

    def test_11_current_state_retrieval(self):
        """Test retrieval of current (most recent) state"""
        alert_id = self._create_test_alert()

        # Add multiple transitions
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, 'Step 1'))
        self.conn.commit()

        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'investigating', self.test_user_id, 'Step 2'))
        self.conn.commit()

        # Get current state
        current_state = self._get_current_state(alert_id)

        self.assertEqual(current_state['state'], 'investigating', "Current state should be 'investigating'")
        self.assertEqual(current_state['notes'], 'Step 2')

    # =============================================================================
    # Test 12: Helper Function - get_current_alert_state
    # =============================================================================

    def test_12_helper_function_get_current_state(self):
        """Test database helper function for getting current state"""
        alert_id = self._create_test_alert()

        # Add a state transition
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, 'Acked'))

        self.conn.commit()

        # Use database helper function
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT get_current_alert_state(%s)", (alert_id,))
            current_state = cursor.fetchone()[0]

        self.assertEqual(current_state, 'acknowledged')

    # =============================================================================
    # Test 13: Helper Function - is_alert_acknowledged
    # =============================================================================

    def test_13_helper_function_is_acknowledged(self):
        """Test database helper function for checking acknowledgement"""
        alert_id = self._create_test_alert()

        # Check before acknowledgement
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT is_alert_acknowledged(%s)", (alert_id,))
            is_acked = cursor.fetchone()[0]

        self.assertFalse(is_acked, "New alert should not be acknowledged")

        # Acknowledge alert
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, 'Acked'))

        self.conn.commit()

        # Check after acknowledgement
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT is_alert_acknowledged(%s)", (alert_id,))
            is_acked = cursor.fetchone()[0]

        self.assertTrue(is_acked, "Acknowledged alert should return True")

    # =============================================================================
    # Test 14: View - v_current_alert_states
    # =============================================================================

    def test_14_view_current_alert_states(self):
        """Test v_current_alert_states view"""
        alert_id = self._create_test_alert(severity='critical')

        # Add state transition
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, 'Acked'))

        self.conn.commit()

        # Query view
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM v_current_alert_states
                WHERE alert_id = %s
            """, (alert_id,))
            view_data = cursor.fetchone()

        self.assertEqual(view_data['alert_id'], alert_id)
        self.assertEqual(view_data['current_state'], 'acknowledged')
        self.assertEqual(view_data['severity'], 'critical')
        self.assertIsNotNone(view_data['tta_target'], "SLA target should be set")

    # =============================================================================
    # Test 15: Metadata Support
    # =============================================================================

    def test_15_metadata_support(self):
        """Test that metadata JSONB field works correctly"""
        alert_id = self._create_test_alert()

        # Add state with metadata
        metadata = {
            'ip_address': '192.168.1.100',
            'browser': 'Chrome',
            'actions_taken': ['checked_logs', 'restarted_service'],
            'estimated_fix_time': 30
        }

        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, 'Acked', psycopg2.extras.Json(metadata)))

        self.conn.commit()

        # Retrieve and verify metadata
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT metadata FROM alert_states
                WHERE alert_id = %s AND state = 'acknowledged'
            """, (alert_id,))
            stored_metadata = cursor.fetchone()['metadata']

        self.assertEqual(stored_metadata['ip_address'], '192.168.1.100')
        self.assertEqual(stored_metadata['estimated_fix_time'], 30)
        self.assertEqual(len(stored_metadata['actions_taken']), 2)


class TestAlertStateMachineEdgeCases(unittest.TestCase):
    """Test suite for edge cases and error scenarios"""

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
        """Set up test data"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO devices (id, name, type, location)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (str(uuid.uuid4()), 'Edge Case Device', 'sensor', 'Test'))
            self.test_device_id = cursor.fetchone()['id']

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO users (id, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (str(uuid.uuid4()), 'edge@example.com', 'hash'))
            self.test_user_id = cursor.fetchone()['id']

        self.conn.commit()

    def tearDown(self):
        """Clean up"""
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM alert_states WHERE alert_id IN (SELECT id FROM alerts WHERE device_id = %s)", (self.test_device_id,))
            cursor.execute("DELETE FROM alert_slas WHERE alert_id IN (SELECT id FROM alerts WHERE device_id = %s)", (self.test_device_id,))
            cursor.execute("DELETE FROM alerts WHERE device_id = %s", (self.test_device_id,))
            cursor.execute("DELETE FROM devices WHERE id = %s", (self.test_device_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (self.test_user_id,))

        self.conn.commit()

    def _create_test_alert(self):
        """Helper: Create test alert"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO alerts (device_id, severity, message)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (self.test_device_id, 'medium', 'Edge case test'))
            return cursor.fetchone()['id']

    # =============================================================================
    # Edge Case Test 1: Invalid State Value
    # =============================================================================

    def test_edge_01_invalid_state_value(self):
        """Test that invalid state values are rejected"""
        alert_id = self._create_test_alert()
        self.conn.commit()

        # Try to insert invalid state
        with self.assertRaises(psycopg2.Error):
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alert_states (alert_id, state, changed_by)
                    VALUES (%s, %s, %s)
                """, (alert_id, 'invalid_state', self.test_user_id))

        self.conn.rollback()

    # =============================================================================
    # Edge Case Test 2: Null Alert ID
    # =============================================================================

    def test_edge_02_null_alert_id(self):
        """Test that null alert_id is rejected"""
        with self.assertRaises(psycopg2.Error):
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alert_states (alert_id, state)
                    VALUES (NULL, %s)
                """, ('new',))

        self.conn.rollback()

    # =============================================================================
    # Edge Case Test 3: Multiple Simultaneous State Changes
    # =============================================================================

    def test_edge_03_multiple_simultaneous_states(self):
        """Test handling of multiple state changes at same time"""
        alert_id = self._create_test_alert()
        self.conn.commit()

        # Add multiple states rapidly
        for state in ['acknowledged', 'investigating', 'resolved']:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alert_states (alert_id, state, changed_by, notes)
                    VALUES (%s, %s, %s, %s)
                """, (alert_id, state, self.test_user_id, f'{state} state'))

        self.conn.commit()

        # Verify all states recorded
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count FROM alert_states
                WHERE alert_id = %s
            """, (alert_id,))
            count = cursor.fetchone()['count']

        self.assertEqual(count, 4, "All states should be recorded (new + 3 transitions)")

    # =============================================================================
    # Edge Case Test 4: Empty Notes
    # =============================================================================

    def test_edge_04_empty_notes(self):
        """Test that empty notes are allowed"""
        alert_id = self._create_test_alert()
        self.conn.commit()

        # Add state with empty notes
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, %s, %s)
            """, (alert_id, 'acknowledged', self.test_user_id, ''))

        self.conn.commit()

        # Verify empty notes stored
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT notes FROM alert_states
                WHERE alert_id = %s AND state = 'acknowledged'
            """, (alert_id,))
            notes = cursor.fetchone()['notes']

        self.assertEqual(notes, '')

    # =============================================================================
    # Edge Case Test 5: Null User (System Action)
    # =============================================================================

    def test_edge_05_null_user_system_action(self):
        """Test that null user is allowed for system actions"""
        alert_id = self._create_test_alert()
        self.conn.commit()

        # Add state with null user (system action)
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alert_states (alert_id, state, changed_by, notes)
                VALUES (%s, %s, NULL, %s)
            """, (alert_id, 'resolved', 'Auto-resolved by system'))

        self.conn.commit()

        # Verify null user accepted
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT changed_by FROM alert_states
                WHERE alert_id = %s AND state = 'resolved'
            """, (alert_id,))
            changed_by = cursor.fetchone()['changed_by']

        self.assertIsNone(changed_by)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAlertStateMachine))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertStateMachineEdgeCases))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY - Alert State Machine")
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

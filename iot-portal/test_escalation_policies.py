#!/usr/bin/env python3
"""
Unit Tests for Escalation Policies
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8
Test-Driven Development (TDD) - Tests written BEFORE implementation

Test Coverage:
1. Policy creation and storage
2. Multi-tier escalation chains
3. Delay/timeout configuration
4. Severity-based policy matching
5. Escalation execution
6. Policy enable/disable
7. Edge cases

Escalation Policy Structure (JSONB):
{
    "tiers": [
        {
            "level": 1,
            "delay_minutes": 0,
            "channels": ["email"],
            "recipients": ["team@example.com"]
        },
        {
            "level": 2,
            "delay_minutes": 5,
            "channels": ["email", "sms"],
            "recipients": ["manager@example.com", "+1234567890"]
        },
        {
            "level": 3,
            "delay_minutes": 15,
            "channels": ["sms", "webhook"],
            "recipients": ["+1234567890", "https://pagerduty.com/webhook"]
        }
    ]
}

Run: python3 test_escalation_policies.py
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


class TestEscalationPolicies(unittest.TestCase):
    """Test suite for escalation policy management"""

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
        # Clean up any existing test policies
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM escalation_policies WHERE name LIKE 'Test%'")
        self.conn.commit()

    def tearDown(self):
        """Clean up test data after each test"""
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM escalation_policies WHERE name LIKE 'Test%'")
        self.conn.commit()

    def _create_test_policy(self, name='Test Policy', severity='critical', enabled=True):
        """Helper: Create a test escalation policy"""
        policy_rules = {
            "tiers": [
                {
                    "level": 1,
                    "delay_minutes": 0,
                    "channels": ["email"],
                    "recipients": ["team@example.com"]
                },
                {
                    "level": 2,
                    "delay_minutes": 5,
                    "channels": ["email", "sms"],
                    "recipients": ["manager@example.com", "+1234567890"]
                },
                {
                    "level": 3,
                    "delay_minutes": 15,
                    "channels": ["sms", "webhook"],
                    "recipients": ["+1234567890", "https://pagerduty.com/webhook"]
                }
            ]
        }

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO escalation_policies (name, description, rules, severities, enabled)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                name,
                f'Test policy for {severity}',
                Json(policy_rules),
                [severity] if severity else ['critical', 'high'],
                enabled
            ))
            policy_id = cursor.fetchone()['id']

        self.conn.commit()
        return policy_id

    def _get_policy(self, policy_id):
        """Helper: Get escalation policy by ID"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM escalation_policies WHERE id = %s
            """, (policy_id,))
            return cursor.fetchone()

    # =============================================================================
    # Test 1: Policy Creation
    # =============================================================================

    def test_01_create_basic_policy(self):
        """Test creating a basic escalation policy"""
        policy_id = self._create_test_policy(name='Test Basic Policy')
        policy = self._get_policy(policy_id)

        self.assertIsNotNone(policy, "Policy should be created")
        self.assertEqual(policy['name'], 'Test Basic Policy')
        self.assertTrue(policy['enabled'], "Policy should be enabled by default")
        self.assertIsNotNone(policy['rules'], "Rules should be stored")
        self.assertIn('critical', policy['severities'], "Should apply to critical severity")

    # =============================================================================
    # Test 2: Multi-Tier Escalation Chain
    # =============================================================================

    def test_02_multi_tier_chain_structure(self):
        """Test that multi-tier escalation chain is stored correctly"""
        policy_id = self._create_test_policy()
        policy = self._get_policy(policy_id)

        rules = policy['rules']
        self.assertIn('tiers', rules, "Rules should contain tiers")
        self.assertEqual(len(rules['tiers']), 3, "Should have 3 escalation tiers")

        # Verify tier 1
        tier1 = rules['tiers'][0]
        self.assertEqual(tier1['level'], 1)
        self.assertEqual(tier1['delay_minutes'], 0)
        self.assertIn('email', tier1['channels'])

        # Verify tier 2
        tier2 = rules['tiers'][1]
        self.assertEqual(tier2['level'], 2)
        self.assertEqual(tier2['delay_minutes'], 5)
        self.assertIn('sms', tier2['channels'])

        # Verify tier 3
        tier3 = rules['tiers'][2]
        self.assertEqual(tier3['level'], 3)
        self.assertEqual(tier3['delay_minutes'], 15)
        self.assertIn('webhook', tier3['channels'])

    # =============================================================================
    # Test 3: Delay Configuration
    # =============================================================================

    def test_03_tier_delay_configuration(self):
        """Test that tier delays are configurable"""
        # Create custom policy with different delays
        custom_rules = {
            "tiers": [
                {"level": 1, "delay_minutes": 0, "channels": ["email"], "recipients": ["a@example.com"]},
                {"level": 2, "delay_minutes": 10, "channels": ["sms"], "recipients": ["+1"]},
                {"level": 3, "delay_minutes": 30, "channels": ["webhook"], "recipients": ["http://x"]}
            ]
        }

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO escalation_policies (name, rules, severities)
                VALUES (%s, %s, %s)
                RETURNING id
            """, ('Test Custom Delays', Json(custom_rules), ['critical']))
            policy_id = cursor.fetchone()['id']
        self.conn.commit()

        policy = self._get_policy(policy_id)
        tiers = policy['rules']['tiers']

        self.assertEqual(tiers[0]['delay_minutes'], 0, "Tier 1 immediate")
        self.assertEqual(tiers[1]['delay_minutes'], 10, "Tier 2 after 10min")
        self.assertEqual(tiers[2]['delay_minutes'], 30, "Tier 3 after 30min")

    # =============================================================================
    # Test 4: Severity-Based Policy Matching
    # =============================================================================

    def test_04_severity_filtering_critical(self):
        """Test policy applies to critical severity"""
        policy_id = self._create_test_policy(severity='critical')
        policy = self._get_policy(policy_id)

        self.assertIn('critical', policy['severities'])
        self.assertNotIn('low', policy['severities'])

    def test_05_severity_filtering_multiple(self):
        """Test policy can apply to multiple severities"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO escalation_policies (name, rules, severities)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (
                'Test Multi-Severity',
                Json({"tiers": [{"level": 1, "delay_minutes": 0, "channels": ["email"], "recipients": ["x"]}]}),
                ['critical', 'high', 'medium']
            ))
            policy_id = cursor.fetchone()['id']
        self.conn.commit()

        policy = self._get_policy(policy_id)
        self.assertEqual(len(policy['severities']), 3)
        self.assertIn('critical', policy['severities'])
        self.assertIn('high', policy['severities'])
        self.assertIn('medium', policy['severities'])

    # =============================================================================
    # Test 6: Channel Configuration
    # =============================================================================

    def test_06_multiple_channels_per_tier(self):
        """Test that tiers can have multiple notification channels"""
        policy_id = self._create_test_policy()
        policy = self._get_policy(policy_id)

        tier2 = policy['rules']['tiers'][1]
        self.assertIn('email', tier2['channels'])
        self.assertIn('sms', tier2['channels'])
        self.assertEqual(len(tier2['channels']), 2)

    # =============================================================================
    # Test 7: Recipient Configuration
    # =============================================================================

    def test_07_recipient_list_storage(self):
        """Test that recipient lists are stored correctly"""
        policy_id = self._create_test_policy()
        policy = self._get_policy(policy_id)

        tier1 = policy['rules']['tiers'][0]
        self.assertIn('team@example.com', tier1['recipients'])

        tier2 = policy['rules']['tiers'][1]
        self.assertIn('manager@example.com', tier2['recipients'])
        self.assertIn('+1234567890', tier2['recipients'])

    # =============================================================================
    # Test 8: Policy Enable/Disable
    # =============================================================================

    def test_08_policy_can_be_disabled(self):
        """Test that policies can be enabled/disabled"""
        policy_id = self._create_test_policy(enabled=False)
        policy = self._get_policy(policy_id)

        self.assertFalse(policy['enabled'], "Policy should be disabled")

        # Enable it
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE escalation_policies
                SET enabled = TRUE
                WHERE id = %s
            """, (policy_id,))
        self.conn.commit()

        policy = self._get_policy(policy_id)
        self.assertTrue(policy['enabled'], "Policy should now be enabled")

    # =============================================================================
    # Test 9: Policy Update
    # =============================================================================

    def test_09_policy_rules_can_be_updated(self):
        """Test that policy rules can be modified"""
        policy_id = self._create_test_policy()

        # Update rules
        new_rules = {
            "tiers": [
                {"level": 1, "delay_minutes": 0, "channels": ["webhook"], "recipients": ["http://new"]}
            ]
        }

        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE escalation_policies
                SET rules = %s
                WHERE id = %s
            """, (Json(new_rules), policy_id))
        self.conn.commit()

        policy = self._get_policy(policy_id)
        self.assertEqual(len(policy['rules']['tiers']), 1, "Should have 1 tier after update")
        self.assertIn('webhook', policy['rules']['tiers'][0]['channels'])

    # =============================================================================
    # Test 10: Query Active Policies by Severity
    # =============================================================================

    def test_10_query_policies_by_severity(self):
        """Test querying policies for a specific severity"""
        # Create policies for different severities
        self._create_test_policy(name='Test Critical Policy', severity='critical')
        self._create_test_policy(name='Test High Policy', severity='high')
        self._create_test_policy(name='Test Medium Policy', severity='medium', enabled=False)

        # Query critical policies
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM escalation_policies
                WHERE 'critical' = ANY(severities)
                AND enabled = TRUE
            """)
            policies = cursor.fetchall()

        self.assertGreaterEqual(len(policies), 1, "Should find at least 1 critical policy")
        critical_policy = next(p for p in policies if p['name'] == 'Test Critical Policy')
        self.assertIn('critical', critical_policy['severities'])

    # =============================================================================
    # Test 11: Unique Policy Names
    # =============================================================================

    def test_11_policy_names_must_be_unique(self):
        """Test that policy names must be unique"""
        self._create_test_policy(name='Test Unique')

        # Try to create another with same name
        with self.assertRaises(psycopg2.Error):
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO escalation_policies (name, rules, severities)
                    VALUES (%s, %s, %s)
                """, (
                    'Test Unique',
                    Json({"tiers": []}),
                    ['critical']
                ))

        self.conn.rollback()

    # =============================================================================
    # Test 12: Timestamp Tracking
    # =============================================================================

    def test_12_timestamps_tracked(self):
        """Test that creation and update timestamps are tracked"""
        policy_id = self._create_test_policy()
        policy = self._get_policy(policy_id)

        self.assertIsNotNone(policy['created_at'], "created_at should be set")
        self.assertIsNotNone(policy['updated_at'], "updated_at should be set")

        created_at = policy['created_at']

        # Update policy
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE escalation_policies
                SET description = 'Updated description'
                WHERE id = %s
            """, (policy_id,))
        self.conn.commit()

        policy = self._get_policy(policy_id)
        self.assertGreaterEqual(policy['updated_at'], created_at, "updated_at should be >= created_at")

    # =============================================================================
    # Test 13: Policy Deletion
    # =============================================================================

    def test_13_policy_can_be_deleted(self):
        """Test that policies can be deleted"""
        policy_id = self._create_test_policy()

        # Verify exists
        policy = self._get_policy(policy_id)
        self.assertIsNotNone(policy)

        # Delete
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM escalation_policies WHERE id = %s", (policy_id,))
        self.conn.commit()

        # Verify deleted
        policy = self._get_policy(policy_id)
        self.assertIsNone(policy, "Policy should be deleted")

    # =============================================================================
    # Test 14: Edge Cases
    # =============================================================================

    def test_14_empty_tier_list(self):
        """Test that empty tier list is allowed (policy can be placeholder)"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO escalation_policies (name, rules, severities)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (
                'Test Empty Tiers',
                Json({"tiers": []}),
                ['critical']
            ))
            policy_id = cursor.fetchone()['id']
        self.conn.commit()

        policy = self._get_policy(policy_id)
        self.assertEqual(len(policy['rules']['tiers']), 0)

    def test_15_null_description(self):
        """Test that description can be null"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                INSERT INTO escalation_policies (name, rules, severities, description)
                VALUES (%s, %s, %s, NULL)
                RETURNING id
            """, (
                'Test Null Description',
                Json({"tiers": []}),
                ['critical']
            ))
            policy_id = cursor.fetchone()['id']
        self.conn.commit()

        policy = self._get_policy(policy_id)
        self.assertIsNone(policy['description'])


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestEscalationPolicies))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY - Escalation Policies")
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

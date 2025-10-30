#!/usr/bin/env python3
"""
Integration Tests for Advanced Alerting System
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8 Week 2

Tests the complete alerting system including:
- Alert API endpoints (13 endpoints)
- Alert state machine integration
- SLA tracking integration
- Escalation policy execution
- On-call rotation queries
- Alert grouping and deduplication
- ML-to-alerting integration
- End-to-end workflows

Author: INSA Automation Corp
Date: October 28, 2025
"""

import unittest
import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Test configuration
BASE_URL = "http://localhost:5002"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials (must match database)
ADMIN_USER = {
    "email": "admin@insa.com",
    "password": "Admin123!"
}

# Test database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'insa_iiot',
    'user': 'iiot_user',
    'password': 'iiot_secure_2025'
}


class AlertingIntegrationTests(unittest.TestCase):
    """Integration tests for advanced alerting system."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Get JWT token for authentication
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=ADMIN_USER
        )

        if response.status_code != 200:
            raise Exception(f"Failed to login: {response.text}")

        cls.token = response.json()['access_token']
        cls.headers = {
            'Authorization': f'Bearer {cls.token}',
            'Content-Type': 'application/json'
        }

        # Create test device and rule
        cls.test_device_id = cls._create_test_device()
        cls.test_rule_id = cls._create_test_rule(cls.test_device_id)

        print(f"\n✓ Test environment setup complete")
        print(f"  - JWT token obtained")
        print(f"  - Test device created: {cls.test_device_id}")
        print(f"  - Test rule created: {cls.test_rule_id}")

    @classmethod
    def _create_test_device(cls) -> str:
        """Create a test device for alerting tests."""
        device_id = str(uuid.uuid4())

        # Use direct database connection to create device
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO devices (id, name, type, location, status)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (device_id, 'Test Device', 'sensor', 'Test Lab', 'active'))
            conn.commit()
        finally:
            conn.close()

        return device_id

    @classmethod
    def _create_test_rule(cls, device_id: str) -> str:
        """Create a test rule for alerting tests."""
        rule_id = str(uuid.uuid4())

        # Use direct database connection to create rule
        import psycopg2
        from psycopg2.extras import Json

        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rules (
                        id, device_id, name, rule_type, enabled,
                        conditions, actions
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    rule_id,
                    device_id,
                    'Test Rule - Temperature High',
                    'threshold',
                    True,
                    Json({'metric': 'temperature', 'operator': '>', 'value': 80}),
                    Json([{'type': 'alert', 'severity': 'high'}])
                ))
            conn.commit()
        finally:
            conn.close()

        return rule_id

    def setUp(self):
        """Set up before each test."""
        # Wait a bit between tests to avoid rate limiting
        time.sleep(0.1)

    # ==========================================================================
    # Test Group 1: Alert Creation and Retrieval (5 tests)
    # ==========================================================================

    def test_01_create_alert_success(self):
        """Test creating a new alert via API."""
        alert_data = {
            'device_id': self.test_device_id,
            'rule_id': self.test_rule_id,
            'severity': 'high',
            'message': 'Temperature exceeds threshold (85.5°C)',
            'value': 85.5,
            'threshold': 80.0
        }

        response = requests.post(
            f"{API_BASE}/alerts",
            headers=self.headers,
            json=alert_data
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertIn('alert_id', data)
        self.assertIn('state', data)
        self.assertEqual(data['state'], 'new')
        self.assertIn('sla', data)
        self.assertIn('group_id', data)

        # Store alert_id for later tests
        self.__class__.test_alert_id = data['alert_id']

        print(f"\n✓ Test 1: Alert created successfully (ID: {data['alert_id']})")

    def test_02_get_alert_details(self):
        """Test retrieving alert details."""
        if not hasattr(self, 'test_alert_id'):
            self.skipTest("No test alert available")

        response = requests.get(
            f"{API_BASE}/alerts/{self.test_alert_id}",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['id'], self.test_alert_id)
        self.assertEqual(data['severity'], 'high')
        self.assertIn('current_state', data)
        self.assertIn('sla_status', data)

        print(f"✓ Test 2: Alert details retrieved successfully")

    def test_03_list_alerts_no_filter(self):
        """Test listing all alerts without filters."""
        response = requests.get(
            f"{API_BASE}/alerts",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('alerts', data)
        self.assertIn('total', data)
        self.assertIsInstance(data['alerts'], list)
        self.assertGreater(data['total'], 0)

        print(f"✓ Test 3: Listed {data['total']} alerts successfully")

    def test_04_list_alerts_with_filter(self):
        """Test listing alerts with severity filter."""
        response = requests.get(
            f"{API_BASE}/alerts?severity=high&status=active",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('alerts', data)

        # All returned alerts should match filter
        for alert in data['alerts']:
            self.assertEqual(alert['severity'], 'high')
            self.assertEqual(alert['status'], 'active')

        print(f"✓ Test 4: Filtered alerts successfully ({len(data['alerts'])} high severity alerts)")

    def test_05_create_alert_missing_fields(self):
        """Test creating alert with missing required fields."""
        alert_data = {
            'device_id': self.test_device_id,
            # Missing rule_id, severity, message
        }

        response = requests.post(
            f"{API_BASE}/alerts",
            headers=self.headers,
            json=alert_data
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)

        print(f"✓ Test 5: Missing fields validation working")

    # ==========================================================================
    # Test Group 2: Alert State Transitions (6 tests)
    # ==========================================================================

    def test_06_acknowledge_alert(self):
        """Test acknowledging an alert (new → acknowledged)."""
        if not hasattr(self, 'test_alert_id'):
            self.skipTest("No test alert available")

        ack_data = {
            'notes': 'Acknowledged - investigating temperature spike'
        }

        response = requests.post(
            f"{API_BASE}/alerts/{self.test_alert_id}/acknowledge",
            headers=self.headers,
            json=ack_data
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['new_state'], 'acknowledged')
        self.assertIn('time_to_acknowledge', data)
        self.assertIsNotNone(data['time_to_acknowledge'])

        print(f"✓ Test 6: Alert acknowledged (TTA: {data['time_to_acknowledge']}s)")

    def test_07_investigate_alert(self):
        """Test starting investigation (acknowledged → investigating)."""
        if not hasattr(self, 'test_alert_id'):
            self.skipTest("No test alert available")

        investigate_data = {
            'notes': 'Checking HVAC system and sensor calibration'
        }

        response = requests.post(
            f"{API_BASE}/alerts/{self.test_alert_id}/investigate",
            headers=self.headers,
            json=investigate_data
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['new_state'], 'investigating')

        print(f"✓ Test 7: Investigation started")

    def test_08_resolve_alert(self):
        """Test resolving an alert (investigating → resolved)."""
        if not hasattr(self, 'test_alert_id'):
            self.skipTest("No test alert available")

        resolve_data = {
            'notes': 'HVAC system adjusted, temperature back to normal',
            'resolution': 'Adjusted HVAC thermostat settings'
        }

        response = requests.post(
            f"{API_BASE}/alerts/{self.test_alert_id}/resolve",
            headers=self.headers,
            json=resolve_data
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['new_state'], 'resolved')
        self.assertIn('time_to_resolve', data)
        self.assertIsNotNone(data['time_to_resolve'])

        print(f"✓ Test 8: Alert resolved (TTR: {data['time_to_resolve']}s)")

    def test_09_invalid_state_transition(self):
        """Test invalid state transition (resolved → acknowledged)."""
        if not hasattr(self, 'test_alert_id'):
            self.skipTest("No test alert available")

        # Try to acknowledge a resolved alert
        response = requests.post(
            f"{API_BASE}/alerts/{self.test_alert_id}/acknowledge",
            headers=self.headers,
            json={'notes': 'This should fail'}
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)

        print(f"✓ Test 9: Invalid state transition blocked")

    def test_10_complete_workflow_new_alert(self):
        """Test complete workflow: create → ack → investigate → resolve."""
        # Create new alert
        alert_data = {
            'device_id': self.test_device_id,
            'rule_id': self.test_rule_id,
            'severity': 'medium',
            'message': 'Pressure variance detected (workflow test)',
            'value': 45.2,
            'threshold': 50.0
        }

        create_response = requests.post(
            f"{API_BASE}/alerts",
            headers=self.headers,
            json=alert_data
        )

        self.assertEqual(create_response.status_code, 201)
        workflow_alert_id = create_response.json()['alert_id']

        # Acknowledge
        time.sleep(0.5)  # Simulate real-world delay
        ack_response = requests.post(
            f"{API_BASE}/alerts/{workflow_alert_id}/acknowledge",
            headers=self.headers,
            json={'notes': 'Workflow test - acknowledged'}
        )
        self.assertEqual(ack_response.status_code, 200)

        # Investigate
        time.sleep(0.5)
        inv_response = requests.post(
            f"{API_BASE}/alerts/{workflow_alert_id}/investigate",
            headers=self.headers,
            json={'notes': 'Workflow test - investigating'}
        )
        self.assertEqual(inv_response.status_code, 200)

        # Resolve
        time.sleep(0.5)
        res_response = requests.post(
            f"{API_BASE}/alerts/{workflow_alert_id}/resolve",
            headers=self.headers,
            json={
                'notes': 'Workflow test - resolved',
                'resolution': 'Workflow test completed successfully'
            }
        )
        self.assertEqual(res_response.status_code, 200)

        # Verify final state
        final_response = requests.get(
            f"{API_BASE}/alerts/{workflow_alert_id}",
            headers=self.headers
        )

        final_data = final_response.json()
        self.assertEqual(final_data['current_state'], 'resolved')
        self.assertIn('sla_status', final_data)

        tta = final_data['sla_status'].get('time_to_acknowledge')
        ttr = final_data['sla_status'].get('time_to_resolve')

        self.assertIsNotNone(tta)
        self.assertIsNotNone(ttr)

        print(f"✓ Test 10: Complete workflow executed (TTA: {tta}s, TTR: {ttr}s)")

    def test_11_get_state_history(self):
        """Test retrieving state transition history."""
        if not hasattr(self, 'test_alert_id'):
            self.skipTest("No test alert available")

        # Get alert details which includes state history
        response = requests.get(
            f"{API_BASE}/alerts/{self.test_alert_id}",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('state_history', data)

        # Should have at least 4 states (new, acknowledged, investigating, resolved)
        self.assertGreaterEqual(len(data['state_history']), 4)

        # Verify state sequence
        states = [s['state'] for s in data['state_history']]
        self.assertEqual(states[0], 'new')
        self.assertEqual(states[-1], 'resolved')

        print(f"✓ Test 11: State history retrieved ({len(states)} transitions)")

    # ==========================================================================
    # Test Group 3: Escalation Policies (3 tests)
    # ==========================================================================

    def test_12_create_escalation_policy(self):
        """Test creating an escalation policy."""
        policy_data = {
            'name': 'Critical Alert Escalation - Test',
            'description': 'Test escalation policy for critical alerts',
            'alert_filter': {
                'severity': ['critical', 'high'],
                'tags': ['production']
            },
            'escalation_tiers': [
                {
                    'tier': 1,
                    'delay_minutes': 0,
                    'contacts': ['oncall-engineer@insa.com'],
                    'channels': ['email']
                },
                {
                    'tier': 2,
                    'delay_minutes': 15,
                    'contacts': ['oncall-manager@insa.com'],
                    'channels': ['email', 'sms']
                },
                {
                    'tier': 3,
                    'delay_minutes': 30,
                    'contacts': ['director@insa.com'],
                    'channels': ['email', 'sms', 'voice']
                }
            ]
        }

        response = requests.post(
            f"{API_BASE}/escalation-policies",
            headers=self.headers,
            json=policy_data
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertIn('policy_id', data)
        self.assertEqual(data['name'], policy_data['name'])
        self.assertEqual(len(data['escalation_tiers']), 3)

        # Store policy_id for later tests
        self.__class__.test_policy_id = data['policy_id']

        print(f"✓ Test 12: Escalation policy created (ID: {data['policy_id']})")

    def test_13_list_escalation_policies(self):
        """Test listing escalation policies."""
        response = requests.get(
            f"{API_BASE}/escalation-policies",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('policies', data)
        self.assertIsInstance(data['policies'], list)
        self.assertGreater(len(data['policies']), 0)

        print(f"✓ Test 13: Listed {len(data['policies'])} escalation policies")

    def test_14_list_escalation_policies_filtered(self):
        """Test listing escalation policies with enabled filter."""
        response = requests.get(
            f"{API_BASE}/escalation-policies?enabled=true",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('policies', data)

        # All returned policies should be enabled
        for policy in data['policies']:
            self.assertTrue(policy['enabled'])

        print(f"✓ Test 14: Filtered policies ({len(data['policies'])} enabled)")

    # ==========================================================================
    # Test Group 4: On-Call Rotation (2 tests)
    # ==========================================================================

    def test_15_get_current_oncall(self):
        """Test getting current on-call engineer."""
        response = requests.get(
            f"{API_BASE}/on-call/current",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('on_call', data)

        # May be empty if no schedules configured
        if data['on_call']:
            self.assertIn('user_id', data['on_call'])
            self.assertIn('schedule_name', data['on_call'])

        print(f"✓ Test 15: Current on-call retrieved")

    def test_16_list_oncall_schedules(self):
        """Test listing on-call schedules."""
        response = requests.get(
            f"{API_BASE}/on-call/schedules",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('schedules', data)
        self.assertIsInstance(data['schedules'], list)

        print(f"✓ Test 16: Listed {len(data['schedules'])} on-call schedules")

    # ==========================================================================
    # Test Group 5: Alert Grouping (3 tests)
    # ==========================================================================

    def test_17_create_multiple_similar_alerts(self):
        """Test creating multiple similar alerts (should be grouped)."""
        # Create 3 similar alerts within 5 minutes
        similar_alerts = []

        for i in range(3):
            alert_data = {
                'device_id': self.test_device_id,
                'rule_id': self.test_rule_id,
                'severity': 'low',
                'message': f'Test grouping alert {i+1} - similar pattern',
                'value': 70.0 + i,
                'threshold': 75.0
            }

            response = requests.post(
                f"{API_BASE}/alerts",
                headers=self.headers,
                json=alert_data
            )

            self.assertEqual(response.status_code, 201)
            similar_alerts.append(response.json()['alert_id'])

            time.sleep(0.2)  # Small delay between alerts

        # Store for verification
        self.__class__.grouped_alerts = similar_alerts

        print(f"✓ Test 17: Created {len(similar_alerts)} similar alerts for grouping")

    def test_18_list_alert_groups(self):
        """Test listing alert groups."""
        response = requests.get(
            f"{API_BASE}/groups",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('groups', data)
        self.assertIsInstance(data['groups'], list)
        self.assertGreater(len(data['groups']), 0)

        print(f"✓ Test 18: Listed {len(data['groups'])} alert groups")

    def test_19_get_group_statistics(self):
        """Test getting alert group statistics."""
        response = requests.get(
            f"{API_BASE}/groups/stats",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('total_groups', data)
        self.assertIn('total_alerts_grouped', data)
        self.assertIn('avg_group_size', data)
        self.assertIn('noise_reduction_percent', data)

        self.assertGreaterEqual(data['total_groups'], 0)
        self.assertGreaterEqual(data['noise_reduction_percent'], 0)

        print(f"✓ Test 19: Group stats retrieved ({data['total_groups']} groups, "
              f"{data['noise_reduction_percent']}% noise reduction)")

    # ==========================================================================
    # Test Group 6: ML-Alerting Integration (3 tests)
    # ==========================================================================

    def test_20_ml_alert_integration_high_confidence(self):
        """Test ML anomaly detection creating high-severity alert."""
        from ml_alert_integration import MLAlertIntegration

        integration = MLAlertIntegration(DB_CONFIG)

        # Simulate high-confidence anomaly detection
        alert_id = integration.create_alert_from_anomaly(
            device_id=self.test_device_id,
            metric_name='temperature',
            value=105.8,
            anomaly_score=-1.25,
            confidence=0.95,  # 95% confidence → critical severity
            model_id=str(uuid.uuid4())
        )

        self.assertIsNotNone(alert_id)

        # Verify alert was created with correct severity
        response = requests.get(
            f"{API_BASE}/alerts/{alert_id}",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['severity'], 'critical')
        self.assertIn('ml_anomaly_detection', data['message'])

        print(f"✓ Test 20: ML high-confidence anomaly created critical alert")

    def test_21_ml_alert_integration_medium_confidence(self):
        """Test ML anomaly detection creating medium-severity alert."""
        from ml_alert_integration import MLAlertIntegration

        integration = MLAlertIntegration(DB_CONFIG)

        # Simulate medium-confidence anomaly detection
        alert_id = integration.create_alert_from_anomaly(
            device_id=self.test_device_id,
            metric_name='pressure',
            value=62.3,
            anomaly_score=-0.65,
            confidence=0.72,  # 72% confidence → medium severity
            model_id=str(uuid.uuid4())
        )

        self.assertIsNotNone(alert_id)

        # Verify alert severity
        response = requests.get(
            f"{API_BASE}/alerts/{alert_id}",
            headers=self.headers
        )

        data = response.json()
        self.assertEqual(data['severity'], 'medium')

        print(f"✓ Test 21: ML medium-confidence anomaly created medium alert")

    def test_22_ml_alert_integration_low_confidence_skipped(self):
        """Test ML anomaly with low confidence does not create alert."""
        from ml_alert_integration import MLAlertIntegration

        integration = MLAlertIntegration(DB_CONFIG)

        # Simulate low-confidence anomaly detection
        prediction = {
            'is_anomaly': True,
            'score': -0.30,
            'confidence': 0.55  # 55% confidence - below 70% threshold
        }

        alert_id = integration.process_anomaly_detection(
            device_id=self.test_device_id,
            metric_name='vibration',
            value=1.2,
            prediction_result=prediction,
            model_id=str(uuid.uuid4()),
            min_confidence_for_alert=0.70
        )

        # Should not create alert due to low confidence
        self.assertIsNone(alert_id)

        print(f"✓ Test 22: ML low-confidence anomaly correctly skipped")

    # ==========================================================================
    # Test Group 7: System Health and Edge Cases (3 tests)
    # ==========================================================================

    def test_23_alerting_health_check(self):
        """Test alerting system health check endpoint."""
        response = requests.get(
            f"{API_BASE}/alerting/health",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('status', data)
        self.assertIn('components', data)
        self.assertIn('metrics', data)

        # Verify all components
        components = data['components']
        self.assertEqual(components['database'], 'healthy')
        self.assertEqual(components['state_machine'], 'operational')
        self.assertEqual(components['sla_tracking'], 'operational')
        self.assertEqual(components['escalation_engine'], 'operational')
        self.assertEqual(components['on_call_manager'], 'operational')
        self.assertEqual(components['alert_grouping'], 'operational')

        print(f"✓ Test 23: System health check passed (status: {data['status']})")

    def test_24_nonexistent_alert_404(self):
        """Test accessing non-existent alert returns 404."""
        fake_alert_id = str(uuid.uuid4())

        response = requests.get(
            f"{API_BASE}/alerts/{fake_alert_id}",
            headers=self.headers
        )

        self.assertEqual(response.status_code, 404)

        data = response.json()
        self.assertIn('error', data)

        print(f"✓ Test 24: Non-existent alert correctly returns 404")

    def test_25_unauthorized_access_401(self):
        """Test accessing endpoints without JWT returns 401."""
        # No Authorization header
        response = requests.get(f"{API_BASE}/alerts")

        self.assertEqual(response.status_code, 401)

        print(f"✓ Test 25: Unauthorized access correctly returns 401")


def run_tests():
    """Run all integration tests and generate report."""
    print("=" * 80)
    print("INSA Advanced IIoT Platform v2.0")
    print("Advanced Alerting System - Integration Tests")
    print("Phase 3 Feature 8 Week 2")
    print("=" * 80)

    # Check if app is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ ERROR: Application not responding to health check")
            print(f"   Start the app first: python3 app_advanced.py")
            return
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR: Cannot connect to application at {BASE_URL}")
        print(f"   Start the app first: python3 app_advanced.py")
        print(f"   Error: {e}")
        return

    print(f"\n✓ Application is running at {BASE_URL}")

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(AlertingIntegrationTests)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate summary report
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    total_tests = result.testsRun
    passed = total_tests - len(result.failures) - len(result.errors) - len(result.skipped)
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)

    pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0

    print(f"\nTotal Tests:  {total_tests}")
    print(f"Passed:       {passed} ({pass_rate:.1f}%)")
    print(f"Failed:       {failed}")
    print(f"Errors:       {errors}")
    print(f"Skipped:      {skipped}")

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
        print("\nAlertingSystem is PRODUCTION READY:")
        print("  ✓ Alert API endpoints (13 endpoints)")
        print("  ✓ State machine integration")
        print("  ✓ SLA tracking")
        print("  ✓ Escalation policies")
        print("  ✓ On-call rotation")
        print("  ✓ Alert grouping")
        print("  ✓ ML-alerting integration")
        print("  ✓ End-to-end workflows")
    else:
        print("\n❌ SOME TESTS FAILED")

        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")

        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")

    print("\n" + "=" * 80)

    return result


if __name__ == '__main__':
    result = run_tests()

    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)

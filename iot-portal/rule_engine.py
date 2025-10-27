#!/usr/bin/env python3
"""
INSA Advanced IIoT Platform - Rule Engine
Automated rule evaluation and action execution

Version: 2.0
Date: October 27, 2025
Author: INSA Automation Corp
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import json
import logging
import uuid
from typing import Dict, List, Any, Optional
import statistics
import re

logger = logging.getLogger(__name__)

class RuleEngine:
    """
    Intelligent rule evaluation engine with automated actions

    Supports 4 rule types:
    1. Threshold rules - Value exceeds/falls below threshold
    2. Comparison rules - Compare two telemetry keys
    3. Time-based rules - Scheduled evaluations (cron)
    4. Statistical rules - Aggregate functions over time windows
    """

    def __init__(self, db_config):
        self.db_config = db_config
        self.scheduler = BackgroundScheduler()
        self.rule_states = {}  # Track rule states to prevent duplicate alerts
        self.running = False

        logger.info("Rule engine initialized")

    def start(self):
        """Start the rule evaluation scheduler"""
        if self.running:
            logger.warning("Rule engine already running")
            return

        # Schedule rule evaluation every 30 seconds
        self.scheduler.add_job(
            self.evaluate_all_rules,
            'interval',
            seconds=30,
            id='rule_evaluation',
            name='Evaluate all rules'
        )

        self.scheduler.start()
        self.running = True
        logger.info("✅ Rule engine started - evaluating every 30 seconds")

    def stop(self):
        """Stop the rule evaluation scheduler"""
        if not self.running:
            return

        self.scheduler.shutdown()
        self.running = False
        logger.info("Rule engine stopped")

    def evaluate_all_rules(self):
        """Evaluate all active rules"""
        try:
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            # Get all active rules
            cur.execute("""
                SELECT * FROM rules
                WHERE enabled = true
                ORDER BY priority DESC
            """)

            rules = cur.fetchall()

            for rule in rules:
                try:
                    self._evaluate_rule(rule)
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule['id']}: {e}")

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error in evaluate_all_rules: {e}")

    def _evaluate_rule(self, rule: Dict[str, Any]):
        """Evaluate a single rule"""
        rule_id = rule['id']
        rule_type = rule['rule_type']
        device_id = rule.get('device_id')
        conditions = rule.get('conditions', {})
        actions = rule.get('actions', [])

        # Evaluate based on rule type
        triggered = False
        context = {}

        if rule_type == 'threshold':
            triggered, context = self._evaluate_threshold_rule(device_id, conditions)

        elif rule_type == 'comparison':
            triggered, context = self._evaluate_comparison_rule(device_id, conditions)

        elif rule_type == 'time_based':
            triggered, context = self._evaluate_time_based_rule(device_id, conditions)

        elif rule_type == 'statistical':
            triggered, context = self._evaluate_statistical_rule(device_id, conditions)

        else:
            logger.warning(f"Unknown rule type: {rule_type}")
            return

        # Check rule state to prevent duplicate alerts
        rule_state_key = f"{rule_id}_{device_id}"
        previous_state = self.rule_states.get(rule_state_key, False)

        # Execute actions only on state change (false → true)
        if triggered and not previous_state:
            logger.info(f"Rule {rule_id} triggered for device {device_id}")
            self._execute_actions(rule, actions, context)

        # Update rule state
        self.rule_states[rule_state_key] = triggered

    def _evaluate_threshold_rule(self, device_id: str, conditions: Dict) -> tuple[bool, Dict]:
        """
        Evaluate threshold rule

        Conditions format:
        {
            "key": "temperature",
            "operator": ">",  # >, <, >=, <=, ==, !=
            "value": 50,
            "duration": 300  # Sustained for 5 minutes (optional)
        }
        """
        try:
            key = conditions.get('key')
            operator = conditions.get('operator')
            threshold = conditions.get('value')
            duration = conditions.get('duration', 0)

            if not all([key, operator, threshold is not None]):
                return False, {}

            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            if duration > 0:
                # Check if condition sustained over duration
                since_time = datetime.now() - timedelta(seconds=duration)

                cur.execute("""
                    SELECT value, timestamp
                    FROM telemetry
                    WHERE device_id = %s AND key = %s AND timestamp >= %s
                    ORDER BY timestamp DESC
                """, (device_id, key, since_time))

                readings = cur.fetchall()

                if not readings:
                    return False, {}

                # All readings must meet the condition
                all_meet_condition = all(
                    self._compare_values(r['value'], operator, threshold)
                    for r in readings
                )

                if all_meet_condition:
                    latest_value = readings[0]['value']
                    return True, {
                        'key': key,
                        'value': latest_value,
                        'threshold': threshold,
                        'operator': operator,
                        'duration': duration,
                        'sustained': True
                    }

                return False, {}

            else:
                # Simple threshold check - latest value
                cur.execute("""
                    SELECT value, timestamp
                    FROM telemetry
                    WHERE device_id = %s AND key = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (device_id, key))

                result = cur.fetchone()

                if result and self._compare_values(result['value'], operator, threshold):
                    return True, {
                        'key': key,
                        'value': result['value'],
                        'threshold': threshold,
                        'operator': operator
                    }

                return False, {}

        except Exception as e:
            logger.error(f"Error evaluating threshold rule: {e}")
            return False, {}
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def _evaluate_comparison_rule(self, device_id: str, conditions: Dict) -> tuple[bool, Dict]:
        """
        Evaluate comparison rule

        Conditions format:
        {
            "key1": "temperature",
            "operator": ">",
            "key2": "setpoint"
        }
        """
        try:
            key1 = conditions.get('key1')
            key2 = conditions.get('key2')
            operator = conditions.get('operator')

            if not all([key1, key2, operator]):
                return False, {}

            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            # Get latest values for both keys
            cur.execute("""
                SELECT key, value
                FROM telemetry
                WHERE device_id = %s AND key IN (%s, %s)
                ORDER BY timestamp DESC
                LIMIT 2
            """, (device_id, key1, key2))

            results = cur.fetchall()

            if len(results) < 2:
                return False, {}

            values = {r['key']: r['value'] for r in results}

            if key1 in values and key2 in values:
                value1 = values[key1]
                value2 = values[key2]

                if self._compare_values(value1, operator, value2):
                    return True, {
                        'key1': key1,
                        'value1': value1,
                        'key2': key2,
                        'value2': value2,
                        'operator': operator
                    }

            return False, {}

        except Exception as e:
            logger.error(f"Error evaluating comparison rule: {e}")
            return False, {}
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def _evaluate_time_based_rule(self, device_id: str, conditions: Dict) -> tuple[bool, Dict]:
        """
        Evaluate time-based rule

        Conditions format:
        {
            "schedule": "0 8 * * *",  # Cron expression
            "check": "device_offline"  # What to check
        }

        Note: Actual cron scheduling would require more complex implementation
        For now, this checks the condition when evaluated
        """
        try:
            check_type = conditions.get('check')

            if check_type == 'device_offline':
                # Check if device has not sent data in last 10 minutes
                conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
                cur = conn.cursor()

                cur.execute("""
                    SELECT last_seen
                    FROM devices
                    WHERE id = %s
                """, (device_id,))

                device = cur.fetchone()

                if device and device['last_seen']:
                    time_since_last_seen = datetime.now() - device['last_seen']
                    if time_since_last_seen.total_seconds() > 600:  # 10 minutes
                        return True, {
                            'check': check_type,
                            'last_seen': device['last_seen'].isoformat(),
                            'offline_duration': time_since_last_seen.total_seconds()
                        }

                cur.close()
                conn.close()

            return False, {}

        except Exception as e:
            logger.error(f"Error evaluating time-based rule: {e}")
            return False, {}
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def _evaluate_statistical_rule(self, device_id: str, conditions: Dict) -> tuple[bool, Dict]:
        """
        Evaluate statistical rule

        Conditions format:
        {
            "key": "temperature",
            "function": "avg",  # avg, max, min, stddev
            "window": 3600,     # 1 hour in seconds
            "operator": ">",
            "value": 45
        }
        """
        try:
            key = conditions.get('key')
            func = conditions.get('function')
            window = conditions.get('window', 3600)
            operator = conditions.get('operator')
            threshold = conditions.get('value')

            if not all([key, func, operator, threshold is not None]):
                return False, {}

            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            # Get values within time window
            since_time = datetime.now() - timedelta(seconds=window)

            cur.execute("""
                SELECT value
                FROM telemetry
                WHERE device_id = %s AND key = %s AND timestamp >= %s
                ORDER BY timestamp DESC
            """, (device_id, key, since_time))

            readings = cur.fetchall()

            if not readings:
                return False, {}

            values = [float(r['value']) for r in readings]

            # Calculate statistical value
            stat_value = None

            if func == 'avg':
                stat_value = statistics.mean(values)
            elif func == 'max':
                stat_value = max(values)
            elif func == 'min':
                stat_value = min(values)
            elif func == 'stddev':
                if len(values) > 1:
                    stat_value = statistics.stdev(values)
                else:
                    return False, {}

            if stat_value is not None:
                if self._compare_values(stat_value, operator, threshold):
                    return True, {
                        'key': key,
                        'function': func,
                        'calculated_value': stat_value,
                        'threshold': threshold,
                        'operator': operator,
                        'window': window,
                        'sample_count': len(values)
                    }

            return False, {}

        except Exception as e:
            logger.error(f"Error evaluating statistical rule: {e}")
            return False, {}
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def _compare_values(self, value1, operator: str, value2) -> bool:
        """Compare two values using specified operator"""
        try:
            v1 = float(value1)
            v2 = float(value2)

            if operator == '>':
                return v1 > v2
            elif operator == '<':
                return v1 < v2
            elif operator == '>=':
                return v1 >= v2
            elif operator == '<=':
                return v1 <= v2
            elif operator == '==':
                return v1 == v2
            elif operator == '!=':
                return v1 != v2
            else:
                return False
        except (ValueError, TypeError):
            return False

    def _execute_actions(self, rule: Dict, actions: List[Dict], context: Dict):
        """Execute rule actions"""
        device_id = rule.get('device_id')
        rule_id = rule.get('id')
        rule_name = rule.get('name', 'Unnamed Rule')

        # Add rule_id to context for action executors
        context['rule_id'] = rule_id

        for action in actions:
            action_type = action.get('type')

            try:
                if action_type == 'alert':
                    self._execute_alert_action(device_id, rule_name, action, context)

                elif action_type == 'email':
                    self._execute_email_action(device_id, rule_name, action, context)

                elif action_type == 'webhook':
                    self._execute_webhook_action(device_id, rule_name, action, context)

                else:
                    logger.warning(f"Unknown action type: {action_type}")

            except Exception as e:
                logger.error(f"Error executing action {action_type}: {e}")

    def _execute_alert_action(self, device_id: str, rule_name: str, action: Dict, context: Dict):
        """Create an alert in the database and emit via WebSocket"""
        try:
            severity = action.get('severity', 'warning')
            message = action.get('message', f'Rule triggered: {rule_name}')

            # Format message with context
            for key, value in context.items():
                message = message.replace(f'{{{key}}}', str(value))

            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            alert_id = str(uuid.uuid4())

            cur.execute("""
                INSERT INTO alerts (id, device_id, rule_id, severity, message, metadata, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'active', NOW())
            """, (alert_id, device_id, context.get('rule_id'), severity, message, json.dumps(context)))

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"Alert created: {severity} - {message}")

            # Emit alert via WebSocket (if available)
            try:
                from socketio_server import get_websocket_server
                ws_server = get_websocket_server()
                if ws_server:
                    ws_server.emit_alert(alert_id, device_id, severity, message, context)
            except:
                pass  # WebSocket not critical

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    def _execute_email_action(self, device_id: str, rule_name: str, action: Dict, context: Dict):
        """Send email notification (placeholder for Feature 4)"""
        logger.info(f"Email action triggered for rule '{rule_name}' (Feature 4 - not yet implemented)")
        # Will be implemented in Feature 4: Email Notification System

    def _execute_webhook_action(self, device_id: str, rule_name: str, action: Dict, context: Dict):
        """Call webhook (placeholder for Feature 5)"""
        logger.info(f"Webhook action triggered for rule '{rule_name}' (Feature 5 - not yet implemented)")
        # Will be implemented in Feature 5: Webhook Action System

# Global instance
_rule_engine = None

def get_rule_engine():
    """Get global rule engine instance"""
    return _rule_engine

def init_rule_engine(db_config):
    """Initialize global rule engine instance"""
    global _rule_engine
    _rule_engine = RuleEngine(db_config)
    return _rule_engine

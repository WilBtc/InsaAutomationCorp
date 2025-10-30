#!/usr/bin/env python3
"""
Escalation Policy Engine
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8: Advanced Alerting

Manages multi-tier alert escalation based on configurable policies.

Features:
- Multi-tier escalation chains (e.g., email → SMS → PagerDuty)
- Configurable delays between tiers (0min, 5min, 15min, 30min)
- Severity-based policy matching
- Multiple notification channels (email, SMS, webhook)
- Escalation state tracking per alert
- Automatic tier progression
- Policy enable/disable support

Escalation Flow:
1. Alert created → Match to policy by severity
2. Execute Tier 1 immediately (delay=0)
3. If not acknowledged after delay → Execute Tier 2
4. If still not acknowledged → Execute Tier 3
5. Continue until alert acknowledged or all tiers exhausted

Example Policy:
{
    "name": "Critical Infrastructure Policy",
    "severities": ["critical"],
    "tiers": [
        {
            "level": 1,
            "delay_minutes": 0,
            "channels": ["email"],
            "recipients": ["ops-team@example.com"]
        },
        {
            "level": 2,
            "delay_minutes": 5,
            "channels": ["email", "sms"],
            "recipients": ["ops-lead@example.com", "+1234567890"]
        },
        {
            "level": 3,
            "delay_minutes": 15,
            "channels": ["sms", "webhook"],
            "recipients": ["+1234567890", "https://api.pagerduty.com/..."]
        }
    ]
}

Author: INSA Automation Corp
Created: October 28, 2025
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EscalationException(Exception):
    """Base exception for escalation engine errors"""
    pass


class PolicyNotFound(EscalationException):
    """Raised when escalation policy is not found"""
    pass


class NoMatchingPolicy(EscalationException):
    """Raised when no policy matches alert severity"""
    pass


class EscalationEngine:
    """
    Escalation Policy Engine

    Manages alert escalation through multi-tier notification chains.

    Responsibilities:
    1. Match alerts to policies based on severity
    2. Execute escalation tiers with configured delays
    3. Track current escalation tier per alert
    4. Send notifications via multiple channels
    5. Automatically progress to next tier if not acknowledged

    Database Schema:
        Table: escalation_policies
        - id: UUID
        - name: VARCHAR(255) UNIQUE
        - description: TEXT
        - rules: JSONB (tier configuration)
        - severities: VARCHAR(20)[] (applicable severities)
        - enabled: BOOLEAN
        - created_at: TIMESTAMP
        - updated_at: TIMESTAMP

        alert_states table tracks current tier via metadata:
        metadata: {"escalation_tier": 2, "policy_id": "uuid"}

    Example Usage:
        >>> from escalation_engine import EscalationEngine
        >>>
        >>> # Initialize
        >>> engine = EscalationEngine(db_config)
        >>>
        >>> # Get policy for alert
        >>> policy = engine.get_policy_for_alert(alert_id='123...')
        >>>
        >>> # Check if escalation needed
        >>> needs_escalation = engine.should_escalate(alert_id='123...')
        >>>
        >>> # Execute escalation
        >>> if needs_escalation:
        ...     engine.escalate_alert(alert_id='123...')
        >>>
        >>> # Get escalation status
        >>> status = engine.get_escalation_status(alert_id='123...')
        >>> print(f"Current tier: {status['current_tier']}/{status['total_tiers']}")
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize Escalation Engine

        Args:
            db_config: PostgreSQL connection configuration
        """
        self.db_config = db_config
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("Escalation Engine: Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Escalation Engine: Database connection failed: {e}")
            raise EscalationException(f"Failed to connect to database: {e}")

    def _ensure_connection(self):
        """Ensure database connection is alive"""
        if self.conn is None or self.conn.closed:
            self._connect()

    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Escalation Engine: Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def get_all_policies(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all escalation policies

        Args:
            enabled_only: Only return enabled policies (default True)

        Returns:
            List of policy dictionaries

        Example:
            >>> policies = engine.get_all_policies()
            >>> for policy in policies:
            ...     print(f"{policy['name']}: {len(policy['rules']['tiers'])} tiers")
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM escalation_policies"
                if enabled_only:
                    query += " WHERE enabled = TRUE"
                query += " ORDER BY name"

                cursor.execute(query)
                return cursor.fetchall()

        except psycopg2.Error as e:
            logger.error(f"Failed to get escalation policies: {e}")
            raise EscalationException(f"Database error: {e}")

    def get_policy_by_id(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get escalation policy by ID

        Args:
            policy_id: UUID of the policy

        Returns:
            Policy dictionary or None if not found
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM escalation_policies WHERE id = %s
                """, (policy_id,))
                return cursor.fetchone()

        except psycopg2.Error as e:
            logger.error(f"Failed to get policy {policy_id}: {e}")
            raise EscalationException(f"Database error: {e}")

    def get_policy_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get escalation policy by name

        Args:
            name: Policy name

        Returns:
            Policy dictionary or None if not found
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM escalation_policies WHERE name = %s
                """, (name,))
                return cursor.fetchone()

        except psycopg2.Error as e:
            logger.error(f"Failed to get policy '{name}': {e}")
            raise EscalationException(f"Database error: {e}")

    def get_policies_for_severity(self, severity: str) -> List[Dict[str, Any]]:
        """
        Get all policies applicable to a severity level

        Args:
            severity: Severity level (critical, high, medium, low, info)

        Returns:
            List of matching policies (enabled only)

        Example:
            >>> policies = engine.get_policies_for_severity('critical')
            >>> print(f"Found {len(policies)} policies for critical alerts")
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM escalation_policies
                    WHERE %s = ANY(severities)
                    AND enabled = TRUE
                    ORDER BY name
                """, (severity,))
                return cursor.fetchall()

        except psycopg2.Error as e:
            logger.error(f"Failed to get policies for severity {severity}: {e}")
            raise EscalationException(f"Database error: {e}")

    def get_policy_for_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the escalation policy for a specific alert

        Matches policy based on alert severity. If multiple policies match,
        returns the first one (alphabetically by name).

        Args:
            alert_id: UUID of the alert

        Returns:
            Matching policy or None if no policy found

        Raises:
            EscalationException: If alert not found
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get alert severity
                cursor.execute("""
                    SELECT severity FROM alerts WHERE id = %s
                """, (alert_id,))
                alert = cursor.fetchone()

                if alert is None:
                    raise EscalationException(f"Alert {alert_id} not found")

                severity = alert['severity']

            # Get policies for this severity
            policies = self.get_policies_for_severity(severity)

            if not policies:
                logger.warning(f"No escalation policy found for severity '{severity}'")
                return None

            # Return first matching policy
            policy = policies[0]
            logger.info(f"Alert {alert_id}: Matched to policy '{policy['name']}'")
            return policy

        except psycopg2.Error as e:
            logger.error(f"Failed to get policy for alert {alert_id}: {e}")
            raise EscalationException(f"Database error: {e}")

    def get_escalation_status(self, alert_id: str) -> Dict[str, Any]:
        """
        Get escalation status for an alert

        Args:
            alert_id: UUID of the alert

        Returns:
            Escalation status:
            {
                'alert_id': 'uuid',
                'policy': {...},  # Policy dict or None
                'current_tier': 1,  # Current escalation tier
                'total_tiers': 3,  # Total tiers in policy
                'next_escalation_at': datetime,  # When next tier executes
                'escalation_complete': False,  # All tiers exhausted
                'current_state': 'new'  # Alert state
            }

        Example:
            >>> status = engine.get_escalation_status('123...')
            >>> print(f"Tier {status['current_tier']} of {status['total_tiers']}")
        """
        self._ensure_connection()

        try:
            # Get alert and current state
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT a.id, a.severity, a.created_at,
                           s.state, s.metadata, s.changed_at
                    FROM alerts a
                    LEFT JOIN alert_states s ON s.id = (
                        SELECT id FROM alert_states
                        WHERE alert_id = a.id
                        ORDER BY changed_at DESC, id DESC
                        LIMIT 1
                    )
                    WHERE a.id = %s
                """, (alert_id,))
                alert = cursor.fetchone()

                if alert is None:
                    raise EscalationException(f"Alert {alert_id} not found")

            # Get policy
            policy = self.get_policy_for_alert(alert_id)

            if policy is None:
                return {
                    'alert_id': alert_id,
                    'policy': None,
                    'current_tier': 0,
                    'total_tiers': 0,
                    'next_escalation_at': None,
                    'escalation_complete': True,
                    'current_state': alert['state']
                }

            # Get current tier from metadata
            metadata = alert['metadata'] or {}
            current_tier = metadata.get('escalation_tier', 0)
            total_tiers = len(policy['rules'].get('tiers', []))

            # Calculate next escalation time
            next_escalation_at = None
            if current_tier < total_tiers:
                next_tier = current_tier + 1
                if next_tier <= total_tiers:
                    tier_config = policy['rules']['tiers'][next_tier - 1]
                    delay_minutes = tier_config['delay_minutes']
                    next_escalation_at = alert['created_at'] + timedelta(minutes=delay_minutes)

            return {
                'alert_id': alert_id,
                'policy': policy,
                'current_tier': current_tier,
                'total_tiers': total_tiers,
                'next_escalation_at': next_escalation_at,
                'escalation_complete': current_tier >= total_tiers,
                'current_state': alert['state']
            }

        except psycopg2.Error as e:
            logger.error(f"Failed to get escalation status for alert {alert_id}: {e}")
            raise EscalationException(f"Database error: {e}")

    def should_escalate(self, alert_id: str) -> bool:
        """
        Check if an alert should be escalated to the next tier

        Args:
            alert_id: UUID of the alert

        Returns:
            True if escalation should occur, False otherwise

        Escalation occurs when:
        1. Alert is not acknowledged/resolved
        2. Enough time has passed for next tier
        3. There are more tiers available

        Example:
            >>> if engine.should_escalate('123...'):
            ...     engine.escalate_alert('123...')
        """
        status = self.get_escalation_status(alert_id)

        # No policy = no escalation
        if status['policy'] is None:
            return False

        # Already acknowledged or resolved = no escalation
        if status['current_state'] in ['acknowledged', 'resolved']:
            return False

        # All tiers exhausted = no escalation
        if status['escalation_complete']:
            return False

        # Check if enough time has passed for next tier
        if status['next_escalation_at'] is None:
            return False

        now = datetime.now()
        return now >= status['next_escalation_at']

    def escalate_alert(self, alert_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Escalate alert to the next tier

        Args:
            alert_id: UUID of the alert
            force: If True, skip time check and escalate immediately

        Returns:
            Escalation result:
            {
                'alert_id': 'uuid',
                'tier': 2,
                'policy': 'Critical Policy',
                'notifications_sent': [
                    {'channel': 'email', 'recipient': 'ops@example.com', 'success': True},
                    {'channel': 'sms', 'recipient': '+1234567890', 'success': True}
                ]
            }

        Raises:
            EscalationException: If escalation cannot be performed

        Example:
            >>> result = engine.escalate_alert('123...')
            >>> print(f"Escalated to tier {result['tier']}")
            >>> print(f"Sent {len(result['notifications_sent'])} notifications")
        """
        self._ensure_connection()

        # Check if escalation should occur
        if not force and not self.should_escalate(alert_id):
            raise EscalationException(f"Alert {alert_id} does not need escalation at this time")

        status = self.get_escalation_status(alert_id)

        if status['policy'] is None:
            raise NoMatchingPolicy(f"No escalation policy found for alert {alert_id}")

        if status['escalation_complete']:
            raise EscalationException(f"Alert {alert_id} has exhausted all escalation tiers")

        # Calculate next tier
        next_tier = status['current_tier'] + 1
        tier_config = status['policy']['rules']['tiers'][next_tier - 1]

        logger.info(
            f"Escalating alert {alert_id} to tier {next_tier} "
            f"(policy: {status['policy']['name']})"
        )

        # Send notifications
        notifications_sent = self._send_tier_notifications(alert_id, tier_config)

        # Update escalation tier in alert metadata
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alert_states (alert_id, state, changed_by, notes, metadata)
                    VALUES (
                        %s,
                        (SELECT state FROM alert_states WHERE alert_id = %s ORDER BY changed_at DESC LIMIT 1),
                        NULL,
                        %s,
                        %s
                    )
                """, (
                    alert_id,
                    alert_id,
                    f"Escalated to tier {next_tier}: {', '.join(tier_config['channels'])}",
                    Json({'escalation_tier': next_tier, 'policy_id': str(status['policy']['id'])})
                ))

            self.conn.commit()

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to update escalation tier for alert {alert_id}: {e}")
            raise EscalationException(f"Database error: {e}")

        return {
            'alert_id': alert_id,
            'tier': next_tier,
            'policy': status['policy']['name'],
            'notifications_sent': notifications_sent
        }

    def _send_tier_notifications(self, alert_id: str, tier_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Send notifications for an escalation tier

        Args:
            alert_id: UUID of the alert
            tier_config: Tier configuration dict

        Returns:
            List of notification results

        Note: This is a placeholder. Actual notification sending will be
              implemented in the notification module (email, SMS, webhook).
        """
        notifications = []

        for channel in tier_config['channels']:
            for recipient in tier_config['recipients']:
                logger.info(
                    f"Sending {channel} notification to {recipient} for alert {alert_id}"
                )

                # Placeholder: Actual notification sending would happen here
                # For now, we just log and mark as successful
                notifications.append({
                    'channel': channel,
                    'recipient': recipient,
                    'success': True,
                    'sent_at': datetime.now()
                })

        return notifications

    def create_policy(
        self,
        name: str,
        rules: Dict[str, Any],
        severities: List[str],
        description: Optional[str] = None,
        enabled: bool = True
    ) -> str:
        """
        Create a new escalation policy

        Args:
            name: Policy name (must be unique)
            rules: Tier configuration (JSONB)
            severities: List of applicable severities
            description: Optional description
            enabled: Enable policy immediately (default True)

        Returns:
            Policy ID (UUID)

        Example:
            >>> policy_id = engine.create_policy(
            ...     name='Critical Infrastructure',
            ...     rules={
            ...         "tiers": [
            ...             {"level": 1, "delay_minutes": 0, "channels": ["email"], "recipients": ["ops@x.com"]},
            ...             {"level": 2, "delay_minutes": 5, "channels": ["sms"], "recipients": ["+1234"]}
            ...         ]
            ...     },
            ...     severities=['critical', 'high']
            ... )
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO escalation_policies (name, description, rules, severities, enabled)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (name, description, Json(rules), severities, enabled))

                policy_id = cursor.fetchone()['id']

            self.conn.commit()

            logger.info(f"Created escalation policy '{name}' (ID: {policy_id})")
            return str(policy_id)

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to create policy '{name}': {e}")
            raise EscalationException(f"Database error: {e}")

    def update_policy(
        self,
        policy_id: str,
        name: Optional[str] = None,
        rules: Optional[Dict[str, Any]] = None,
        severities: Optional[List[str]] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update an escalation policy

        Args:
            policy_id: UUID of policy to update
            name: New name (optional)
            rules: New tier configuration (optional)
            severities: New severity list (optional)
            description: New description (optional)
            enabled: Enable/disable policy (optional)

        Returns:
            Updated policy dictionary

        Example:
            >>> engine.update_policy(
            ...     policy_id='123...',
            ...     enabled=False  # Disable policy
            ... )
        """
        self._ensure_connection()

        try:
            # Build UPDATE statement dynamically
            updates = []
            params = []

            if name is not None:
                updates.append("name = %s")
                params.append(name)

            if rules is not None:
                updates.append("rules = %s")
                params.append(Json(rules))

            if severities is not None:
                updates.append("severities = %s")
                params.append(severities)

            if description is not None:
                updates.append("description = %s")
                params.append(description)

            if enabled is not None:
                updates.append("enabled = %s")
                params.append(enabled)

            if not updates:
                raise ValueError("No updates provided")

            params.append(policy_id)

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = f"""
                    UPDATE escalation_policies
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING *
                """
                cursor.execute(query, params)

                result = cursor.fetchone()

                if result is None:
                    raise PolicyNotFound(f"Policy {policy_id} not found")

            self.conn.commit()

            logger.info(f"Updated escalation policy '{result['name']}' (ID: {policy_id})")
            return result

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to update policy {policy_id}: {e}")
            raise EscalationException(f"Database error: {e}")

    def delete_policy(self, policy_id: str) -> bool:
        """
        Delete an escalation policy

        Args:
            policy_id: UUID of policy to delete

        Returns:
            True if deleted, False if not found

        Example:
            >>> engine.delete_policy('123...')
            True
        """
        self._ensure_connection()

        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM escalation_policies WHERE id = %s
                """, (policy_id,))

                deleted = cursor.rowcount > 0

            self.conn.commit()

            if deleted:
                logger.info(f"Deleted escalation policy {policy_id}")
            else:
                logger.warning(f"Policy {policy_id} not found for deletion")

            return deleted

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to delete policy {policy_id}: {e}")
            raise EscalationException(f"Database error: {e}")


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

    # Example: Escalation engine usage
    with EscalationEngine(DB_CONFIG) as engine:
        # Get all policies
        policies = engine.get_all_policies()
        print(f"\n{len(policies)} escalation policies found:")
        for policy in policies:
            tiers = len(policy['rules'].get('tiers', []))
            severities = ', '.join(policy['severities'])
            print(f"  - {policy['name']}: {tiers} tiers ({severities})")

        # Example: Check escalation status
        try:
            alert_id = '123e4567-e89b-12d3-a456-426614174000'
            status = engine.get_escalation_status(alert_id)
            print(f"\nAlert {alert_id}:")
            print(f"  Current tier: {status['current_tier']}/{status['total_tiers']}")
            print(f"  Escalation complete: {status['escalation_complete']}")
        except Exception as e:
            print(f"Alert example requires valid alert_id: {e}")

#!/usr/bin/env python3
"""
Alert State Machine
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8: Advanced Alerting

Manages alert lifecycle state transitions:
- new → acknowledged → investigating → resolved
- new → investigating → resolved (skip acknowledge)
- new → acknowledged → resolved (quick fix)

Features:
- State validation and enforcement
- State history tracking
- User tracking (RBAC integration)
- Notes attachment
- Metadata support (JSONB)
- PostgreSQL backend with triggers

Author: INSA Automation Corp
Created: October 28, 2025
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertStateException(Exception):
    """Base exception for alert state machine errors"""
    pass


class InvalidStateTransition(AlertStateException):
    """Raised when an invalid state transition is attempted"""
    pass


class AlertNotFound(AlertStateException):
    """Raised when alert ID does not exist"""
    pass


class AlertStateMachine:
    """
    Alert State Machine

    Manages alert lifecycle state transitions with full audit trail.

    Valid States:
        - new: Initial state (auto-created by database trigger)
        - acknowledged: Operator has seen the alert
        - investigating: Actively diagnosing the issue
        - resolved: Issue has been fixed

    Valid Transitions:
        - new → acknowledged → investigating → resolved (full lifecycle)
        - new → investigating → resolved (skip acknowledge)
        - new → acknowledged → resolved (quick fix)
        - new → resolved (auto-resolved by system)

    Database Schema:
        Table: alert_states
        - id: UUID (primary key)
        - alert_id: UUID (foreign key to alerts)
        - state: VARCHAR(50) CHECK (state IN ('new', 'acknowledged', 'investigating', 'resolved'))
        - changed_by: UUID (foreign key to users, nullable for system actions)
        - changed_at: TIMESTAMP (auto-set by database)
        - notes: TEXT (optional)
        - metadata: JSONB (optional structured data)

    Example Usage:
        >>> from alert_state_machine import AlertStateMachine
        >>>
        >>> # Initialize
        >>> state_machine = AlertStateMachine(db_config)
        >>>
        >>> # Acknowledge alert
        >>> state_machine.transition_state(
        ...     alert_id='123e4567-e89b-12d3-a456-426614174000',
        ...     new_state='acknowledged',
        ...     user_id='550e8400-e29b-41d4-a716-446655440000',
        ...     notes='Investigating temperature spike'
        ... )
        >>>
        >>> # Get current state
        >>> current = state_machine.get_current_state(alert_id)
        >>> print(current['state'])  # 'acknowledged'
        >>>
        >>> # Get full history
        >>> history = state_machine.get_state_history(alert_id)
        >>> for state in history:
        ...     print(f"{state['state']} at {state['changed_at']} by {state['changed_by']}")
    """

    # Valid states
    STATE_NEW = 'new'
    STATE_ACKNOWLEDGED = 'acknowledged'
    STATE_INVESTIGATING = 'investigating'
    STATE_RESOLVED = 'resolved'

    VALID_STATES = {STATE_NEW, STATE_ACKNOWLEDGED, STATE_INVESTIGATING, STATE_RESOLVED}

    # Valid state transitions (from_state → to_state)
    VALID_TRANSITIONS = {
        STATE_NEW: {STATE_ACKNOWLEDGED, STATE_INVESTIGATING, STATE_RESOLVED},
        STATE_ACKNOWLEDGED: {STATE_INVESTIGATING, STATE_RESOLVED},
        STATE_INVESTIGATING: {STATE_RESOLVED},
        STATE_RESOLVED: set()  # Terminal state, no transitions allowed
    }

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize Alert State Machine

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
            logger.info("Alert State Machine: Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Alert State Machine: Database connection failed: {e}")
            raise AlertStateException(f"Failed to connect to database: {e}")

    def _ensure_connection(self):
        """Ensure database connection is alive"""
        if self.conn is None or self.conn.closed:
            self._connect()

    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Alert State Machine: Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def get_current_state(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current (most recent) state of an alert

        Args:
            alert_id: UUID of the alert

        Returns:
            Dictionary with state details:
            {
                'state': 'acknowledged',
                'changed_by': 'user-uuid',
                'changed_at': datetime,
                'notes': 'Investigating...',
                'metadata': {...}
            }

            Returns None if alert has no states

        Raises:
            AlertNotFound: If alert_id does not exist
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if alert exists
                cursor.execute("SELECT id FROM alerts WHERE id = %s", (alert_id,))
                if cursor.fetchone() is None:
                    raise AlertNotFound(f"Alert {alert_id} not found")

                # Get current state
                cursor.execute("""
                    SELECT state, changed_by, changed_at, notes, metadata
                    FROM alert_states
                    WHERE alert_id = %s
                    ORDER BY changed_at DESC, id DESC
                    LIMIT 1
                """, (alert_id,))

                return cursor.fetchone()

        except psycopg2.Error as e:
            logger.error(f"Failed to get current state for alert {alert_id}: {e}")
            raise AlertStateException(f"Database error: {e}")

    def get_state_history(self, alert_id: str) -> List[Dict[str, Any]]:
        """
        Get complete state history for an alert

        Args:
            alert_id: UUID of the alert

        Returns:
            List of state dictionaries in chronological order (oldest first):
            [
                {
                    'id': 'state-uuid',
                    'state': 'new',
                    'changed_by': None,
                    'changed_at': datetime,
                    'notes': 'Alert created by system',
                    'metadata': {}
                },
                {
                    'id': 'state-uuid',
                    'state': 'acknowledged',
                    'changed_by': 'user-uuid',
                    'changed_at': datetime,
                    'notes': 'Investigating...',
                    'metadata': {...}
                },
                ...
            ]

        Raises:
            AlertNotFound: If alert_id does not exist
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if alert exists
                cursor.execute("SELECT id FROM alerts WHERE id = %s", (alert_id,))
                if cursor.fetchone() is None:
                    raise AlertNotFound(f"Alert {alert_id} not found")

                # Get all states in chronological order
                cursor.execute("""
                    SELECT id, state, changed_by, changed_at, notes, metadata
                    FROM alert_states
                    WHERE alert_id = %s
                    ORDER BY changed_at ASC, id ASC
                """, (alert_id,))

                return cursor.fetchall()

        except psycopg2.Error as e:
            logger.error(f"Failed to get state history for alert {alert_id}: {e}")
            raise AlertStateException(f"Database error: {e}")

    def is_valid_transition(self, current_state: str, new_state: str) -> bool:
        """
        Check if a state transition is valid

        Args:
            current_state: Current state (new, acknowledged, investigating, resolved)
            new_state: Desired new state

        Returns:
            True if transition is valid, False otherwise

        Example:
            >>> state_machine.is_valid_transition('new', 'acknowledged')  # True
            >>> state_machine.is_valid_transition('resolved', 'new')  # False
        """
        if current_state not in self.VALID_STATES:
            return False
        if new_state not in self.VALID_STATES:
            return False

        return new_state in self.VALID_TRANSITIONS.get(current_state, set())

    def transition_state(
        self,
        alert_id: str,
        new_state: str,
        user_id: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Transition alert to a new state

        Args:
            alert_id: UUID of the alert
            new_state: New state (acknowledged, investigating, resolved)
            user_id: UUID of user making the change (None for system actions)
            notes: Optional notes about the state change
            metadata: Optional metadata (stored as JSONB)
            force: If True, skip validation (use with caution!)

        Returns:
            Dictionary with new state details

        Raises:
            AlertNotFound: If alert_id does not exist
            InvalidStateTransition: If transition is not valid

        Example:
            >>> state_machine.transition_state(
            ...     alert_id='123...',
            ...     new_state='acknowledged',
            ...     user_id='456...',
            ...     notes='Investigating temperature spike',
            ...     metadata={'ip_address': '192.168.1.100', 'browser': 'Chrome'}
            ... )
        """
        self._ensure_connection()

        # Validate new state
        if new_state not in self.VALID_STATES:
            raise InvalidStateTransition(
                f"Invalid state '{new_state}'. Must be one of: {', '.join(self.VALID_STATES)}"
            )

        # Get current state (if exists)
        current = self.get_current_state(alert_id)

        # If no current state, we can't transition (initial state is auto-created by trigger)
        if current is None:
            raise AlertStateException(
                f"Alert {alert_id} has no current state. This should not happen - "
                "initial state is auto-created by database trigger."
            )

        current_state = current['state']

        # Validate transition (unless force=True)
        if not force and not self.is_valid_transition(current_state, new_state):
            raise InvalidStateTransition(
                f"Invalid transition from '{current_state}' to '{new_state}'. "
                f"Valid transitions from '{current_state}': {', '.join(self.VALID_TRANSITIONS[current_state]) if self.VALID_TRANSITIONS[current_state] else 'none (terminal state)'}"
            )

        # Insert new state
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO alert_states (alert_id, state, changed_by, notes, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, state, changed_by, changed_at, notes, metadata
                """, (
                    alert_id,
                    new_state,
                    user_id,
                    notes,
                    Json(metadata) if metadata else None
                ))

                new_state_record = cursor.fetchone()

            self.conn.commit()

            logger.info(
                f"Alert {alert_id}: State transition {current_state} → {new_state} "
                f"by user {user_id or 'system'}"
            )

            return new_state_record

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to transition alert {alert_id} to {new_state}: {e}")
            raise AlertStateException(f"Database error: {e}")

    def acknowledge(
        self,
        alert_id: str,
        user_id: str,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method: Acknowledge an alert

        Args:
            alert_id: UUID of the alert
            user_id: UUID of user acknowledging the alert
            notes: Optional notes
            metadata: Optional metadata

        Returns:
            New state record
        """
        return self.transition_state(
            alert_id=alert_id,
            new_state=self.STATE_ACKNOWLEDGED,
            user_id=user_id,
            notes=notes or "Alert acknowledged",
            metadata=metadata
        )

    def start_investigation(
        self,
        alert_id: str,
        user_id: str,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method: Start investigating an alert

        Args:
            alert_id: UUID of the alert
            user_id: UUID of user starting investigation
            notes: Optional notes
            metadata: Optional metadata

        Returns:
            New state record
        """
        return self.transition_state(
            alert_id=alert_id,
            new_state=self.STATE_INVESTIGATING,
            user_id=user_id,
            notes=notes or "Investigation started",
            metadata=metadata
        )

    def resolve(
        self,
        alert_id: str,
        user_id: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method: Resolve an alert

        Args:
            alert_id: UUID of the alert
            user_id: UUID of user resolving the alert (None for auto-resolve)
            notes: Optional notes
            metadata: Optional metadata

        Returns:
            New state record
        """
        return self.transition_state(
            alert_id=alert_id,
            new_state=self.STATE_RESOLVED,
            user_id=user_id,
            notes=notes or ("Alert resolved" if user_id else "Auto-resolved by system"),
            metadata=metadata
        )

    def add_note(
        self,
        alert_id: str,
        user_id: str,
        notes: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a note to an alert without changing state

        This creates a new state record with the same state as current,
        allowing notes to be added to the audit trail.

        Args:
            alert_id: UUID of the alert
            user_id: UUID of user adding the note
            notes: Note text (required)
            metadata: Optional metadata

        Returns:
            New state record (same state as current)

        Raises:
            ValueError: If notes is empty
        """
        if not notes or not notes.strip():
            raise ValueError("Notes cannot be empty when adding a note")

        # Get current state
        current = self.get_current_state(alert_id)
        if current is None:
            raise AlertStateException(f"Alert {alert_id} has no current state")

        # Insert new record with same state
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO alert_states (alert_id, state, changed_by, notes, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, state, changed_by, changed_at, notes, metadata
                """, (
                    alert_id,
                    current['state'],  # Same state as current
                    user_id,
                    notes,
                    Json(metadata) if metadata else None
                ))

                new_record = cursor.fetchone()

            self.conn.commit()

            logger.info(f"Alert {alert_id}: Note added by user {user_id}")

            return new_record

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to add note to alert {alert_id}: {e}")
            raise AlertStateException(f"Database error: {e}")


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

    # Example: Use as context manager
    with AlertStateMachine(DB_CONFIG) as state_machine:
        # Get current state
        alert_id = '123e4567-e89b-12d3-a456-426614174000'

        try:
            current = state_machine.get_current_state(alert_id)
            print(f"Current state: {current['state']}")

            # Acknowledge alert
            state_machine.acknowledge(
                alert_id=alert_id,
                user_id='550e8400-e29b-41d4-a716-446655440000',
                notes='Investigating temperature spike'
            )

            # Get history
            history = state_machine.get_state_history(alert_id)
            for state in history:
                print(f"{state['state']} at {state['changed_at']} by {state['changed_by']}")

        except AlertNotFound:
            print(f"Alert {alert_id} not found - create test data first")
        except Exception as e:
            print(f"Error: {e}")

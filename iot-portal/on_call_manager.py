#!/usr/bin/env python3
"""
On-Call Schedule Manager
INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8: Advanced Alerting

Manages on-call rotation schedules for 24/7 alert coverage.

Features:
- Weekly/daily rotation support
- Timezone-aware scheduling
- Current on-call calculation
- Temporary overrides (vacation, holidays)
- Multiple rotation schedules
- User rotation order management

Rotation Types:
- Weekly: Each user on-call for 1 week
- Daily: Each user on-call for 1 day

Schedule Structure (JSONB):
{
    "rotation_type": "weekly",  // or "daily"
    "rotation_start": "2025-10-28T00:00:00Z",  // Start of rotation
    "users": [
        {"id": "user-uuid-1", "order": 1},
        {"id": "user-uuid-2", "order": 2},
        {"id": "user-uuid-3", "order": 3}
    ],
    "overrides": [  // Optional temporary assignments
        {
            "user_id": "user-uuid-4",
            "start": "2025-11-01T00:00:00Z",
            "end": "2025-11-07T23:59:59Z",
            "reason": "Vacation coverage"
        }
    ]
}

Example:
    3-person weekly rotation starting Oct 28, 2025:
    - Week 1 (Oct 28 - Nov 3): User 1
    - Week 2 (Nov 4 - Nov 10): User 2
    - Week 3 (Nov 11 - Nov 17): User 3
    - Week 4 (Nov 18 - Nov 24): User 1 (cycle repeats)

Author: INSA Automation Corp
Created: October 28, 2025
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import pytz
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OnCallException(Exception):
    """Base exception for on-call manager errors"""
    pass


class ScheduleNotFound(OnCallException):
    """Raised when schedule is not found"""
    pass


class InvalidSchedule(OnCallException):
    """Raised when schedule configuration is invalid"""
    pass


class OnCallManager:
    """
    On-Call Schedule Manager

    Manages on-call rotation schedules and calculates current on-call user.

    Responsibilities:
    1. Create/update/delete on-call schedules
    2. Calculate who is on-call at any given time
    3. Handle timezone conversions
    4. Support temporary overrides (vacation, holidays)
    5. Track multiple concurrent schedules

    Database Schema:
        Table: on_call_schedules
        - id: UUID
        - name: VARCHAR(255) UNIQUE
        - description: TEXT
        - schedule: JSONB (rotation configuration)
        - timezone: VARCHAR(50) (e.g., 'UTC', 'America/New_York')
        - enabled: BOOLEAN
        - created_at: TIMESTAMP
        - updated_at: TIMESTAMP

    Example Usage:
        >>> from on_call_manager import OnCallManager
        >>>
        >>> # Initialize
        >>> manager = OnCallManager(db_config)
        >>>
        >>> # Create schedule
        >>> schedule_id = manager.create_schedule(
        ...     name='Ops Team Rotation',
        ...     rotation_type='weekly',
        ...     users=[user1_id, user2_id, user3_id],
        ...     timezone='America/New_York'
        ... )
        >>>
        >>> # Get current on-call user
        >>> current = manager.get_current_on_call(schedule_id)
        >>> print(f"On-call: {current['user_id']}")
        >>>
        >>> # Check who's on-call at a specific time
        >>> future_time = datetime.now() + timedelta(days=7)
        >>> future_on_call = manager.get_on_call_at(schedule_id, future_time)
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize On-Call Manager

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
            logger.info("On-Call Manager: Database connection established")
        except psycopg2.Error as e:
            logger.error(f"On-Call Manager: Database connection failed: {e}")
            raise OnCallException(f"Failed to connect to database: {e}")

    def _ensure_connection(self):
        """Ensure database connection is alive"""
        if self.conn is None or self.conn.closed:
            self._connect()

    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("On-Call Manager: Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def get_all_schedules(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all on-call schedules

        Args:
            enabled_only: Only return enabled schedules (default True)

        Returns:
            List of schedule dictionaries
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM on_call_schedules"
                if enabled_only:
                    query += " WHERE enabled = TRUE"
                query += " ORDER BY name"

                cursor.execute(query)
                return cursor.fetchall()

        except psycopg2.Error as e:
            logger.error(f"Failed to get on-call schedules: {e}")
            raise OnCallException(f"Database error: {e}")

    def get_schedule_by_id(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get on-call schedule by ID

        Args:
            schedule_id: UUID of the schedule

        Returns:
            Schedule dictionary or None if not found
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM on_call_schedules WHERE id = %s
                """, (schedule_id,))
                return cursor.fetchone()

        except psycopg2.Error as e:
            logger.error(f"Failed to get schedule {schedule_id}: {e}")
            raise OnCallException(f"Database error: {e}")

    def get_schedule_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get on-call schedule by name

        Args:
            name: Schedule name

        Returns:
            Schedule dictionary or None if not found
        """
        self._ensure_connection()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM on_call_schedules WHERE name = %s
                """, (name,))
                return cursor.fetchone()

        except psycopg2.Error as e:
            logger.error(f"Failed to get schedule '{name}': {e}")
            raise OnCallException(f"Database error: {e}")

    def create_schedule(
        self,
        name: str,
        rotation_type: str,
        users: List[str],
        timezone: str = 'UTC',
        rotation_start: Optional[datetime] = None,
        description: Optional[str] = None,
        enabled: bool = True
    ) -> str:
        """
        Create a new on-call schedule

        Args:
            name: Schedule name (must be unique)
            rotation_type: 'weekly' or 'daily'
            users: List of user IDs in rotation order
            timezone: Timezone (e.g., 'UTC', 'America/New_York')
            rotation_start: Start date/time (defaults to now)
            description: Optional description
            enabled: Enable schedule immediately (default True)

        Returns:
            Schedule ID (UUID)

        Example:
            >>> schedule_id = manager.create_schedule(
            ...     name='Ops Team Weekly',
            ...     rotation_type='weekly',
            ...     users=['user1-uuid', 'user2-uuid', 'user3-uuid'],
            ...     timezone='America/New_York'
            ... )
        """
        self._ensure_connection()

        if rotation_type not in ['weekly', 'daily']:
            raise InvalidSchedule(f"Invalid rotation type '{rotation_type}'. Must be 'weekly' or 'daily'")

        if not users:
            raise InvalidSchedule("User list cannot be empty")

        # Default rotation start to now
        if rotation_start is None:
            rotation_start = datetime.now(pytz.UTC)

        # Build schedule configuration
        schedule_config = {
            "rotation_type": rotation_type,
            "rotation_start": rotation_start.isoformat(),
            "users": [
                {"id": str(user_id), "order": i + 1}
                for i, user_id in enumerate(users)
            ]
        }

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO on_call_schedules (name, description, schedule, timezone, enabled)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (name, description, Json(schedule_config), timezone, enabled))

                schedule_id = cursor.fetchone()['id']

            self.conn.commit()

            logger.info(
                f"Created on-call schedule '{name}' "
                f"(ID: {schedule_id}, {rotation_type}, {len(users)} users)"
            )
            return str(schedule_id)

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to create schedule '{name}': {e}")
            raise OnCallException(f"Database error: {e}")

    def get_current_on_call(self, schedule_id: str) -> Dict[str, Any]:
        """
        Get current on-call user for a schedule

        Args:
            schedule_id: UUID of the schedule

        Returns:
            On-call information:
            {
                'user_id': 'user-uuid',
                'user_order': 2,
                'shift_start': datetime,
                'shift_end': datetime,
                'is_override': False,
                'override_reason': None
            }

        Raises:
            ScheduleNotFound: If schedule not found
            InvalidSchedule: If schedule is malformed

        Example:
            >>> current = manager.get_current_on_call('schedule-uuid')
            >>> print(f"On-call: User {current['user_id']}")
            >>> print(f"Shift: {current['shift_start']} to {current['shift_end']}")
        """
        return self.get_on_call_at(schedule_id, datetime.now(pytz.UTC))

    def get_on_call_at(self, schedule_id: str, check_time: datetime) -> Dict[str, Any]:
        """
        Get on-call user at a specific time

        Args:
            schedule_id: UUID of the schedule
            check_time: Time to check (timezone-aware)

        Returns:
            On-call information (same format as get_current_on_call)

        Example:
            >>> # Who will be on-call next week?
            >>> future_time = datetime.now() + timedelta(days=7)
            >>> future_on_call = manager.get_on_call_at('schedule-uuid', future_time)
        """
        self._ensure_connection()

        schedule = self.get_schedule_by_id(schedule_id)

        if schedule is None:
            raise ScheduleNotFound(f"Schedule {schedule_id} not found")

        if not schedule['enabled']:
            raise InvalidSchedule(f"Schedule {schedule_id} is disabled")

        config = schedule['schedule']

        # Ensure check_time is timezone-aware
        if check_time.tzinfo is None:
            check_time = pytz.UTC.localize(check_time)

        # Convert to schedule timezone
        schedule_tz = pytz.timezone(schedule['timezone'])
        check_time = check_time.astimezone(schedule_tz)

        # Check for overrides first
        if 'overrides' in config:
            for override in config['overrides']:
                override_start = datetime.fromisoformat(override['start'])
                override_end = datetime.fromisoformat(override['end'])

                if override_start.tzinfo is None:
                    override_start = schedule_tz.localize(override_start)
                if override_end.tzinfo is None:
                    override_end = schedule_tz.localize(override_end)

                if override_start <= check_time <= override_end:
                    return {
                        'user_id': override['user_id'],
                        'user_order': None,
                        'shift_start': override_start,
                        'shift_end': override_end,
                        'is_override': True,
                        'override_reason': override.get('reason', 'Manual override')
                    }

        # Calculate normal rotation
        users = config['users']
        if not users:
            raise InvalidSchedule(f"Schedule {schedule_id} has no users in rotation")

        rotation_start = datetime.fromisoformat(config['rotation_start'])
        if rotation_start.tzinfo is None:
            rotation_start = schedule_tz.localize(rotation_start)

        rotation_type = config['rotation_type']

        # Calculate which user is on-call
        if rotation_type == 'weekly':
            # Calculate weeks since rotation start
            time_diff = check_time - rotation_start
            weeks_passed = time_diff.days // 7
            user_index = weeks_passed % len(users)

            # Calculate shift boundaries
            shift_start = rotation_start + timedelta(weeks=weeks_passed)
            shift_end = shift_start + timedelta(weeks=1) - timedelta(seconds=1)

        elif rotation_type == 'daily':
            # Calculate days since rotation start
            time_diff = check_time - rotation_start
            days_passed = time_diff.days
            user_index = days_passed % len(users)

            # Calculate shift boundaries
            shift_start = rotation_start + timedelta(days=days_passed)
            shift_start = shift_start.replace(hour=0, minute=0, second=0, microsecond=0)
            shift_end = shift_start + timedelta(days=1) - timedelta(seconds=1)

        else:
            raise InvalidSchedule(f"Unknown rotation type '{rotation_type}'")

        on_call_user = users[user_index]

        return {
            'user_id': on_call_user['id'],
            'user_order': on_call_user['order'],
            'shift_start': shift_start,
            'shift_end': shift_end,
            'is_override': False,
            'override_reason': None
        }

    def add_override(
        self,
        schedule_id: str,
        user_id: str,
        start: datetime,
        end: datetime,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add temporary on-call override

        Args:
            schedule_id: UUID of the schedule
            user_id: User to assign during override
            start: Override start time
            end: Override end time
            reason: Optional reason (e.g., "Vacation coverage")

        Returns:
            Updated schedule dictionary

        Example:
            >>> # Cover vacation for user who's normally on-call
            >>> manager.add_override(
            ...     schedule_id='schedule-uuid',
            ...     user_id='replacement-user-uuid',
            ...     start=datetime(2025, 12, 20),
            ...     end=datetime(2025, 12, 27),
            ...     reason='Holiday vacation coverage'
            ... )
        """
        self._ensure_connection()

        schedule = self.get_schedule_by_id(schedule_id)

        if schedule is None:
            raise ScheduleNotFound(f"Schedule {schedule_id} not found")

        config = schedule['schedule']

        # Add override
        if 'overrides' not in config:
            config['overrides'] = []

        config['overrides'].append({
            "user_id": str(user_id),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "reason": reason or "Manual override"
        })

        # Update schedule
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    UPDATE on_call_schedules
                    SET schedule = %s
                    WHERE id = %s
                    RETURNING *
                """, (Json(config), schedule_id))

                result = cursor.fetchone()

            self.conn.commit()

            logger.info(
                f"Added override to schedule {schedule_id}: "
                f"User {user_id} from {start} to {end}"
            )
            return result

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to add override to schedule {schedule_id}: {e}")
            raise OnCallException(f"Database error: {e}")

    def update_schedule(
        self,
        schedule_id: str,
        name: Optional[str] = None,
        users: Optional[List[str]] = None,
        timezone: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update an on-call schedule

        Args:
            schedule_id: UUID of schedule to update
            name: New name (optional)
            users: New user rotation list (optional)
            timezone: New timezone (optional)
            description: New description (optional)
            enabled: Enable/disable schedule (optional)

        Returns:
            Updated schedule dictionary
        """
        self._ensure_connection()

        schedule = self.get_schedule_by_id(schedule_id)

        if schedule is None:
            raise ScheduleNotFound(f"Schedule {schedule_id} not found")

        # Build update statement dynamically
        updates = []
        params = []

        if name is not None:
            updates.append("name = %s")
            params.append(name)

        if users is not None:
            # Update users in schedule config
            config = schedule['schedule']
            config['users'] = [
                {"id": str(user_id), "order": i + 1}
                for i, user_id in enumerate(users)
            ]
            updates.append("schedule = %s")
            params.append(Json(config))

        if timezone is not None:
            updates.append("timezone = %s")
            params.append(timezone)

        if description is not None:
            updates.append("description = %s")
            params.append(description)

        if enabled is not None:
            updates.append("enabled = %s")
            params.append(enabled)

        if not updates:
            raise ValueError("No updates provided")

        params.append(schedule_id)

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = f"""
                    UPDATE on_call_schedules
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING *
                """
                cursor.execute(query, params)

                result = cursor.fetchone()

            self.conn.commit()

            logger.info(f"Updated on-call schedule '{result['name']}' (ID: {schedule_id})")
            return result

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to update schedule {schedule_id}: {e}")
            raise OnCallException(f"Database error: {e}")

    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete an on-call schedule

        Args:
            schedule_id: UUID of schedule to delete

        Returns:
            True if deleted, False if not found
        """
        self._ensure_connection()

        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM on_call_schedules WHERE id = %s
                """, (schedule_id,))

                deleted = cursor.rowcount > 0

            self.conn.commit()

            if deleted:
                logger.info(f"Deleted on-call schedule {schedule_id}")
            else:
                logger.warning(f"Schedule {schedule_id} not found for deletion")

            return deleted

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to delete schedule {schedule_id}: {e}")
            raise OnCallException(f"Database error: {e}")


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

    # Example: On-call manager usage
    with OnCallManager(DB_CONFIG) as manager:
        # Get all schedules
        schedules = manager.get_all_schedules()
        print(f"\n{len(schedules)} on-call schedules found:")
        for schedule in schedules:
            users = len(schedule['schedule'].get('users', []))
            rotation = schedule['schedule'].get('rotation_type', 'unknown')
            print(f"  - {schedule['name']}: {rotation} rotation, {users} users")

        # Example: Get current on-call (requires valid schedule)
        if schedules:
            schedule_id = schedules[0]['id']
            try:
                current = manager.get_current_on_call(schedule_id)
                print(f"\nCurrent on-call for '{schedules[0]['name']}':")
                print(f"  User: {current['user_id']}")
                print(f"  Shift: {current['shift_start']} to {current['shift_end']}")
                print(f"  Override: {current['is_override']}")
            except Exception as e:
                print(f"Could not get current on-call: {e}")

#!/usr/bin/env python3
"""
Dead Letter Queue for INSA CRM Multi-Agent System
Stores messages that fail processing after all retries, allowing manual replay and failure analytics

Features:
- SQLite-based persistent storage
- Failed message capture with error details
- Manual replay functionality
- Failure analytics (by topic, by error type)
- Status tracking (failed, replayed)
- Retention policies
"""
import sqlite3
import json
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DeadLetter:
    """Represents a message in the Dead Letter Queue"""
    id: Optional[int] = None
    topic: str = ""
    message: str = ""
    original_timestamp: float = 0.0
    failed_timestamp: float = 0.0
    error_type: str = ""
    error_message: str = ""
    retry_count: int = 0
    status: str = "failed"  # failed, replayed, archived
    replayed_at: Optional[float] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeadLetter':
        """Create from dictionary"""
        return cls(**data)


class DeadLetterQueue:
    """
    Dead Letter Queue for failed messages

    Features:
    - Persistent SQLite storage
    - Message replay functionality
    - Failure analytics and reporting
    - Retention policies
    """

    def __init__(self, db_path: str = "/var/lib/insa-crm/dead_letter_queue.db"):
        """
        Initialize Dead Letter Queue

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
        logger.info(f"Dead Letter Queue initialized (database: {db_path})")

    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dead_letters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    message TEXT NOT NULL,
                    original_timestamp REAL NOT NULL,
                    failed_timestamp REAL NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'failed',
                    replayed_at REAL,
                    notes TEXT
                )
            """)

            # Create indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_topic ON dead_letters(topic)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON dead_letters(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_error_type ON dead_letters(error_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_failed_timestamp ON dead_letters(failed_timestamp)")

            conn.commit()

    def add_message(
        self,
        topic: str,
        message: Any,
        error: Exception,
        retry_count: int = 0,
        original_timestamp: Optional[float] = None,
        notes: str = ""
    ) -> int:
        """
        Add a failed message to the Dead Letter Queue

        Args:
            topic: Message topic/queue name
            message: Message content (will be JSON-serialized if dict/list)
            error: Exception that caused the failure
            retry_count: Number of retry attempts that were made
            original_timestamp: When message was originally created
            notes: Additional notes about the failure

        Returns:
            ID of the inserted dead letter
        """
        # Serialize message if it's a dict/list
        if isinstance(message, (dict, list)):
            message_str = json.dumps(message)
        else:
            message_str = str(message)

        # Get error details
        error_type = type(error).__name__
        error_message = str(error)

        # Timestamps
        failed_timestamp = time.time()
        if original_timestamp is None:
            original_timestamp = failed_timestamp

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO dead_letters (
                    topic, message, original_timestamp, failed_timestamp,
                    error_type, error_message, retry_count, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'failed', ?)
            """, (
                topic, message_str, original_timestamp, failed_timestamp,
                error_type, error_message, retry_count, notes
            ))
            conn.commit()
            dlq_id = cursor.lastrowid

        logger.warning(
            f"Message added to DLQ (id: {dlq_id}, topic: {topic}, error: {error_type}, "
            f"retries: {retry_count})"
        )

        return dlq_id

    def get_failed_messages(
        self,
        topic: Optional[str] = None,
        error_type: Optional[str] = None,
        status: str = "failed",
        limit: int = 100,
        offset: int = 0
    ) -> List[DeadLetter]:
        """
        Get failed messages from the DLQ

        Args:
            topic: Filter by topic (optional)
            error_type: Filter by error type (optional)
            status: Filter by status (default: 'failed')
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of DeadLetter objects
        """
        query = "SELECT * FROM dead_letters WHERE 1=1"
        params = []

        if topic:
            query += " AND topic = ?"
            params.append(topic)

        if error_type:
            query += " AND error_type = ?"
            params.append(error_type)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY failed_timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_dead_letter(row) for row in rows]

    def get_message_by_id(self, dlq_id: int) -> Optional[DeadLetter]:
        """
        Get a specific message by ID

        Args:
            dlq_id: Dead letter ID

        Returns:
            DeadLetter object or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM dead_letters WHERE id = ?", (dlq_id,))
            row = cursor.fetchone()

        return self._row_to_dead_letter(row) if row else None

    def replay_message(self, dlq_id: int, replay_callback: callable) -> bool:
        """
        Replay a failed message

        Args:
            dlq_id: Dead letter ID to replay
            replay_callback: Function to call with (topic, message) to replay

        Returns:
            True if replay succeeded, False otherwise
        """
        dead_letter = self.get_message_by_id(dlq_id)
        if not dead_letter:
            logger.error(f"Dead letter {dlq_id} not found")
            return False

        if dead_letter.status == "replayed":
            logger.warning(f"Dead letter {dlq_id} already replayed")
            return False

        try:
            # Parse message if it's JSON
            try:
                message = json.loads(dead_letter.message)
            except json.JSONDecodeError:
                message = dead_letter.message

            # Replay the message
            replay_callback(dead_letter.topic, message)

            # Mark as replayed
            self._mark_replayed(dlq_id)

            logger.info(f"✅ Dead letter {dlq_id} replayed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to replay dead letter {dlq_id}: {e}")
            return False

    def _mark_replayed(self, dlq_id: int):
        """Mark a message as replayed"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE dead_letters
                SET status = 'replayed', replayed_at = ?
                WHERE id = ?
            """, (time.time(), dlq_id))
            conn.commit()

    def update_notes(self, dlq_id: int, notes: str):
        """
        Update notes for a dead letter

        Args:
            dlq_id: Dead letter ID
            notes: New notes text
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE dead_letters SET notes = ? WHERE id = ?", (notes, dlq_id))
            conn.commit()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get DLQ analytics and statistics

        Returns:
            Dictionary with statistics:
            - total_messages: Total count
            - by_status: Count by status
            - by_topic: Count by topic
            - by_error_type: Count by error type
            - oldest_message: Timestamp of oldest message
            - newest_message: Timestamp of newest message
        """
        with sqlite3.connect(self.db_path) as conn:
            # Total messages
            total = conn.execute("SELECT COUNT(*) FROM dead_letters").fetchone()[0]

            # By status
            by_status = {}
            cursor = conn.execute("SELECT status, COUNT(*) FROM dead_letters GROUP BY status")
            for status, count in cursor.fetchall():
                by_status[status] = count

            # By topic
            by_topic = {}
            cursor = conn.execute("SELECT topic, COUNT(*) FROM dead_letters GROUP BY topic ORDER BY COUNT(*) DESC LIMIT 10")
            for topic, count in cursor.fetchall():
                by_topic[topic] = count

            # By error type
            by_error_type = {}
            cursor = conn.execute("SELECT error_type, COUNT(*) FROM dead_letters GROUP BY error_type ORDER BY COUNT(*) DESC LIMIT 10")
            for error_type, count in cursor.fetchall():
                by_error_type[error_type] = count

            # Timestamps
            cursor = conn.execute("SELECT MIN(failed_timestamp), MAX(failed_timestamp) FROM dead_letters")
            oldest, newest = cursor.fetchone()

        return {
            'total_messages': total,
            'by_status': by_status,
            'by_topic': by_topic,
            'by_error_type': by_error_type,
            'oldest_message': datetime.fromtimestamp(oldest).isoformat() if oldest else None,
            'newest_message': datetime.fromtimestamp(newest).isoformat() if newest else None
        }

    def delete_old_messages(self, days: int = 30, status: str = "replayed") -> int:
        """
        Delete old messages (retention policy)

        Args:
            days: Delete messages older than this many days
            status: Only delete messages with this status

        Returns:
            Number of messages deleted
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM dead_letters
                WHERE failed_timestamp < ? AND status = ?
            """, (cutoff_time, status))
            conn.commit()
            deleted_count = cursor.rowcount

        logger.info(f"Deleted {deleted_count} old messages (status: {status}, older than {days} days)")
        return deleted_count

    def _row_to_dead_letter(self, row: sqlite3.Row) -> DeadLetter:
        """Convert database row to DeadLetter object"""
        return DeadLetter(
            id=row['id'],
            topic=row['topic'],
            message=row['message'],
            original_timestamp=row['original_timestamp'],
            failed_timestamp=row['failed_timestamp'],
            error_type=row['error_type'],
            error_message=row['error_message'],
            retry_count=row['retry_count'],
            status=row['status'],
            replayed_at=row['replayed_at'],
            notes=row['notes']
        )


# Global DLQ instance
_dlq_instance: Optional[DeadLetterQueue] = None


def get_dead_letter_queue(db_path: str = "/var/lib/insa-crm/dead_letter_queue.db") -> DeadLetterQueue:
    """
    Get or create global Dead Letter Queue instance

    Args:
        db_path: Path to SQLite database file

    Returns:
        DeadLetterQueue instance
    """
    global _dlq_instance
    if _dlq_instance is None:
        _dlq_instance = DeadLetterQueue(db_path)
    return _dlq_instance


if __name__ == '__main__':
    # Demo: Test Dead Letter Queue
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("DEAD LETTER QUEUE DEMO")
    print("=" * 60)

    # Create DLQ with temporary database
    import tempfile
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    dlq = DeadLetterQueue(db_file.name)

    # Example 1: Add failed messages
    print("\n1. Adding failed messages...")

    msg1 = {"customer_id": "CUST-001", "action": "create_quote"}
    dlq.add_message(
        topic="quote_generation",
        message=msg1,
        error=ValueError("Invalid customer ID"),
        retry_count=5
    )

    msg2 = {"lead_id": "LEAD-123", "status": "qualified"}
    dlq.add_message(
        topic="lead_processing",
        message=msg2,
        error=ConnectionError("Database unavailable"),
        retry_count=3
    )

    msg3 = {"order_id": "ORD-456", "total": 15000}
    dlq.add_message(
        topic="order_processing",
        message=msg3,
        error=ValueError("Invalid order total"),
        retry_count=2
    )

    # Example 2: Get statistics
    print("\n2. DLQ Statistics:")
    stats = dlq.get_statistics()
    print(f"   Total messages: {stats['total_messages']}")
    print(f"   By status: {stats['by_status']}")
    print(f"   By topic: {stats['by_topic']}")
    print(f"   By error type: {stats['by_error_type']}")

    # Example 3: Get failed messages
    print("\n3. Getting failed messages...")
    failed = dlq.get_failed_messages(limit=10)
    for dl in failed:
        print(f"   ID {dl.id}: {dl.topic} - {dl.error_type} (retries: {dl.retry_count})")

    # Example 4: Replay a message
    print("\n4. Replaying message...")

    def replay_handler(topic, message):
        print(f"   Replaying: {topic} -> {message}")

    dlq.replay_message(1, replay_handler)

    # Example 5: Get statistics after replay
    print("\n5. Statistics after replay:")
    stats = dlq.get_statistics()
    print(f"   By status: {stats['by_status']}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)

    # Cleanup
    import os
    os.unlink(db_file.name)

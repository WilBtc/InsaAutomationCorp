#!/usr/bin/env python3
"""
Agent Message Bus - Inter-Agent Communication System
Part of Phase 11: Multi-Agent Collaboration

Enables agents to communicate via pub/sub, request/response, and broadcast patterns.
"""
import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from agent_retry import with_retry, DATABASE_RETRY_CONFIG
from dead_letter_queue import get_dead_letter_queue

logger = logging.getLogger(__name__)


class AgentMessageBus:
    """
    Central message bus for inter-agent communication

    Features:
    - Pub/sub pattern (agents subscribe to topics)
    - Request/response pattern (agent A asks agent B)
    - Broadcast pattern (agent A notifies all)
    - Message history (complete audit trail)
    - Retry mechanism (failed messages)
    """

    def __init__(self, db_path: str = '/var/lib/insa-crm/agent_messages.db'):
        """
        Initialize Agent Message Bus

        Args:
            db_path: Path to SQLite database for message persistence
        """
        self.db_path = db_path
        self.subscribers: Dict[str, List[str]] = {}  # topic -> [agent_ids]

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

        # Initialize Dead Letter Queue for permanently failed messages
        self.dlq = get_dead_letter_queue()

        logger.info(f"AgentMessageBus initialized with database: {db_path}")

    def _init_db(self):
        """Create database tables for message persistence"""
        with sqlite3.connect(self.db_path) as conn:
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT,
                    topic TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    error_message TEXT
                )
            """)

            # Subscriptions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(agent_id, topic)
                )
            """)

            # Indices for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_to_agent_status
                ON agent_messages(to_agent, status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topic
                ON agent_messages(topic)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON agent_messages(created_at DESC)
            """)

            conn.commit()
            logger.info("Agent message bus database initialized")

    @with_retry(DATABASE_RETRY_CONFIG)
    def send_message(self, from_agent: str, to_agent: str,
                    topic: str, payload: Dict[str, Any]) -> int:
        """
        Send direct message from one agent to another

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            topic: Message topic/category
            payload: Message data (will be JSON serialized)

        Returns:
            Message ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO agent_messages
                (from_agent, to_agent, topic, message_type, payload, status)
                VALUES (?, ?, ?, 'direct', ?, 'pending')
            """, (from_agent, to_agent, topic, json.dumps(payload)))

            message_id = cursor.lastrowid
            conn.commit()

            logger.debug(f"Message {message_id} sent: {from_agent} → {to_agent} (topic: {topic})")
            return message_id

    def broadcast(self, from_agent: str, topic: str,
                 payload: Dict[str, Any]) -> List[int]:
        """
        Broadcast message to all subscribers of a topic

        Args:
            from_agent: Sender agent ID
            topic: Topic to broadcast to
            payload: Message data

        Returns:
            List of message IDs (one per subscriber)
        """
        message_ids = []

        # Get all subscribers for this topic
        subscribers = self.get_subscribers(topic)

        # Send to each subscriber (except sender)
        for subscriber in subscribers:
            if subscriber != from_agent:
                msg_id = self.send_message(
                    from_agent=from_agent,
                    to_agent=subscriber,
                    topic=topic,
                    payload=payload
                )
                message_ids.append(msg_id)

        logger.info(f"Broadcast from {from_agent} to {len(message_ids)} subscribers (topic: {topic})")
        return message_ids

    @with_retry(DATABASE_RETRY_CONFIG)
    def subscribe(self, agent_id: str, topic: str):
        """
        Subscribe agent to a topic

        Args:
            agent_id: Agent ID to subscribe
            topic: Topic to subscribe to
        """
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO agent_subscriptions (agent_id, topic)
                    VALUES (?, ?)
                """, (agent_id, topic))
                conn.commit()

                # Update in-memory cache
                if topic not in self.subscribers:
                    self.subscribers[topic] = []
                if agent_id not in self.subscribers[topic]:
                    self.subscribers[topic].append(agent_id)

                logger.info(f"Agent {agent_id} subscribed to topic: {topic}")
            except sqlite3.IntegrityError:
                # Already subscribed
                logger.debug(f"Agent {agent_id} already subscribed to {topic}")

    def unsubscribe(self, agent_id: str, topic: str):
        """
        Unsubscribe agent from a topic

        Args:
            agent_id: Agent ID to unsubscribe
            topic: Topic to unsubscribe from
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM agent_subscriptions
                WHERE agent_id = ? AND topic = ?
            """, (agent_id, topic))
            conn.commit()

            # Update in-memory cache
            if topic in self.subscribers and agent_id in self.subscribers[topic]:
                self.subscribers[topic].remove(agent_id)

            logger.info(f"Agent {agent_id} unsubscribed from topic: {topic}")

    def get_subscribers(self, topic: str) -> List[str]:
        """
        Get all subscribers for a topic

        Args:
            topic: Topic to query

        Returns:
            List of agent IDs subscribed to topic
        """
        # Check in-memory cache first
        if topic in self.subscribers:
            return self.subscribers[topic].copy()

        # Load from database
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT agent_id FROM agent_subscriptions
                WHERE topic = ?
            """, (topic,)).fetchall()

            subscribers = [row[0] for row in rows]
            self.subscribers[topic] = subscribers
            return subscribers

    @with_retry(DATABASE_RETRY_CONFIG)
    def get_pending_messages(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all pending messages for an agent

        Args:
            agent_id: Agent ID to query
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM agent_messages
                WHERE to_agent = ? AND status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
            """, (agent_id, limit)).fetchall()

            messages = []
            for row in rows:
                messages.append({
                    'id': row['id'],
                    'from_agent': row['from_agent'],
                    'to_agent': row['to_agent'],
                    'topic': row['topic'],
                    'message_type': row['message_type'],
                    'payload': json.loads(row['payload']),
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'retry_count': row['retry_count']
                })

            logger.debug(f"Retrieved {len(messages)} pending messages for {agent_id}")
            return messages

    @with_retry(DATABASE_RETRY_CONFIG)
    def mark_processed(self, message_id: int, success: bool = True, error_message: str = None):
        """
        Mark message as processed

        Args:
            message_id: Message ID to update
            success: Whether processing succeeded
            error_message: Error message if processing failed
        """
        with sqlite3.connect(self.db_path) as conn:
            if success:
                conn.execute("""
                    UPDATE agent_messages
                    SET status = 'processed', processed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (message_id,))
            else:
                conn.execute("""
                    UPDATE agent_messages
                    SET status = 'failed', error_message = ?,
                        retry_count = retry_count + 1
                    WHERE id = ?
                """, (error_message, message_id))

            conn.commit()
            logger.debug(f"Message {message_id} marked as {'processed' if success else 'failed'}")

    def retry_failed_messages(self, max_retries: int = 3) -> int:
        """
        Retry failed messages that haven't exceeded max retries

        Args:
            max_retries: Maximum number of retries

        Returns:
            Number of messages reset to pending
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE agent_messages
                SET status = 'pending'
                WHERE status = 'failed' AND retry_count < ?
            """, (max_retries,))

            retried = cursor.rowcount
            conn.commit()

            if retried > 0:
                logger.info(f"Reset {retried} failed messages to pending for retry")

            return retried

    def send_failed_to_dlq(self, max_retries: int = 5) -> int:
        """
        Send permanently failed messages (exceeded max retries) to Dead Letter Queue

        Args:
            max_retries: Messages with retry_count >= this go to DLQ

        Returns:
            Number of messages sent to DLQ
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get permanently failed messages
            rows = conn.execute("""
                SELECT * FROM agent_messages
                WHERE status = 'failed' AND retry_count >= ?
            """, (max_retries,)).fetchall()

            sent_count = 0
            for row in rows:
                try:
                    # Add to DLQ
                    self.dlq.add_message(
                        topic=row['topic'],
                        message=json.loads(row['payload']),
                        error=Exception(row['error_message'] or "Unknown error"),
                        retry_count=row['retry_count'],
                        original_timestamp=datetime.fromisoformat(row['created_at']).timestamp(),
                        notes=f"Message bus delivery failed (from: {row['from_agent']}, to: {row['to_agent']})"
                    )

                    # Mark as sent to DLQ
                    conn.execute("""
                        UPDATE agent_messages
                        SET status = 'sent_to_dlq'
                        WHERE id = ?
                    """, (row['id'],))

                    sent_count += 1

                except Exception as e:
                    logger.error(f"Failed to send message {row['id']} to DLQ: {e}")

            conn.commit()

            if sent_count > 0:
                logger.info(f"📮 Sent {sent_count} permanently failed messages to DLQ")

            return sent_count

    def get_message_history(self, agent_id: Optional[str] = None,
                           topic: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get message history with optional filters

        Args:
            agent_id: Filter by sender or receiver
            topic: Filter by topic
            limit: Maximum messages to return

        Returns:
            List of message dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Build query with optional filters
            query = "SELECT * FROM agent_messages WHERE 1=1"
            params = []

            if agent_id:
                query += " AND (from_agent = ? OR to_agent = ?)"
                params.extend([agent_id, agent_id])

            if topic:
                query += " AND topic = ?"
                params.append(topic)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            messages = []
            for row in rows:
                messages.append({
                    'id': row['id'],
                    'from_agent': row['from_agent'],
                    'to_agent': row['to_agent'],
                    'topic': row['topic'],
                    'message_type': row['message_type'],
                    'payload': json.loads(row['payload']),
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'processed_at': row['processed_at']
                })

            return messages

    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics

        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            stats = {}

            # Total messages
            stats['total_messages'] = conn.execute(
                "SELECT COUNT(*) FROM agent_messages"
            ).fetchone()[0]

            # Messages by status
            status_counts = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM agent_messages
                GROUP BY status
            """).fetchall()
            stats['by_status'] = {row[0]: row[1] for row in status_counts}

            # Top topics
            topic_counts = conn.execute("""
                SELECT topic, COUNT(*) as count
                FROM agent_messages
                GROUP BY topic
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            stats['top_topics'] = {row[0]: row[1] for row in topic_counts}

            # Active agents
            stats['unique_agents'] = conn.execute("""
                SELECT COUNT(DISTINCT from_agent)
                FROM agent_messages
            """).fetchone()[0]

            # Total subscriptions
            stats['total_subscriptions'] = conn.execute(
                "SELECT COUNT(*) FROM agent_subscriptions"
            ).fetchone()[0]

            return stats

    def cleanup_old_messages(self, days: int = 30) -> int:
        """
        Delete processed messages older than specified days

        Args:
            days: Number of days to keep messages

        Returns:
            Number of messages deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM agent_messages
                WHERE status = 'processed'
                AND processed_at < datetime('now', '-' || ? || ' days')
            """, (days,))

            deleted = cursor.rowcount
            conn.commit()

            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old messages (older than {days} days)")

            return deleted


# Global message bus instance
_message_bus = None


def get_message_bus(db_path: str = '/var/lib/insa-crm/agent_messages.db') -> AgentMessageBus:
    """
    Get or create global message bus instance

    Args:
        db_path: Path to SQLite database

    Returns:
        AgentMessageBus instance
    """
    global _message_bus
    if _message_bus is None:
        _message_bus = AgentMessageBus(db_path)
    return _message_bus


if __name__ == '__main__':
    # Quick test
    logging.basicConfig(level=logging.INFO)

    bus = get_message_bus()

    # Test subscriptions
    bus.subscribe('sizing_agent', 'equipment_dimensioned')
    bus.subscribe('crm_agent', 'equipment_dimensioned')

    # Test direct message
    msg_id = bus.send_message(
        from_agent='sizing_agent',
        to_agent='crm_agent',
        topic='quote_request',
        payload={'equipment': 'separator', 'dimensions': {'diameter': 60, 'length': 20}}
    )
    print(f"Sent message ID: {msg_id}")

    # Test broadcast
    msg_ids = bus.broadcast(
        from_agent='sizing_agent',
        topic='equipment_dimensioned',
        payload={'equipment': 'separator', 'status': 'complete'}
    )
    print(f"Broadcast to {len(msg_ids)} subscribers")

    # Test retrieval
    messages = bus.get_pending_messages('crm_agent')
    print(f"Pending messages for CRM agent: {len(messages)}")

    # Test stats
    stats = bus.get_stats()
    print(f"Message bus stats: {stats}")

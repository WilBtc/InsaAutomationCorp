#!/usr/bin/env python3
"""
Session Manager for INSA Voice Assistant
Provides persistent conversation storage using SQLite
"""
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages conversation sessions with SQLite persistence
    """

    def __init__(self, db_path: str = "/var/lib/insa-crm/conversation_sessions.db"):
        """
        Initialize session manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

        logger.info(f"SessionManager initialized with database: {db_path}")

    def _init_db(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            # Check if sessions table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sessions'
            """)
            table_exists = cursor.fetchone() is not None

            if table_exists:
                # Check if user_id column exists
                cursor = conn.execute("PRAGMA table_info(sessions)")
                columns = [row[1] for row in cursor.fetchall()]

                if 'user_id' not in columns:
                    # Add user_id column to existing table
                    logger.info("Migrating sessions table: Adding user_id column")
                    conn.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER")
                    logger.info("Migration complete: user_id column added")
            else:
                # Create new table with user_id column
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        last_agent TEXT,
                        last_query TEXT,
                        context TEXT,
                        sizing_session TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            # Create indices for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_updated_at
                ON sessions(updated_at)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id
                ON sessions(user_id)
            """)

            conn.commit()
            logger.info("Database tables initialized")

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session data for a given session ID

        Args:
            session_id: Unique session identifier (e.g., user IP or device ID)

        Returns:
            Session dictionary with conversation state
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()

            if row:
                # Deserialize JSON fields
                session = {
                    'last_agent': row['last_agent'],
                    'last_query': row['last_query'],
                    'context': json.loads(row['context'] or '{}'),
                    'sizing_session': json.loads(row['sizing_session'] or '{}')
                }
                logger.debug(f"Retrieved session {session_id}")
                return session
            else:
                # Return empty session
                logger.debug(f"No session found for {session_id}, creating new")
                return self._empty_session()

    def save_session(self, session_id: str, session_data: Dict[str, Any], user_id: int = None):
        """
        Save or update session data

        Args:
            session_id: Unique session identifier
            session_data: Session dictionary to save
            user_id: User ID (optional, for authenticated sessions)
        """
        with sqlite3.connect(self.db_path) as conn:
            # Serialize JSON fields
            context_json = json.dumps(session_data.get('context', {}))
            sizing_json = json.dumps(session_data.get('sizing_session', {}))

            conn.execute("""
                INSERT INTO sessions (
                    session_id, user_id, last_agent, last_query, context,
                    sizing_session, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    last_agent = excluded.last_agent,
                    last_query = excluded.last_query,
                    context = excluded.context,
                    sizing_session = excluded.sizing_session,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                session_id,
                user_id,
                session_data.get('last_agent'),
                session_data.get('last_query'),
                context_json,
                sizing_json
            ))

            conn.commit()
            logger.debug(f"Saved session {session_id} for user {user_id}")

    def delete_session(self, session_id: str):
        """
        Delete a session

        Args:
            session_id: Session to delete
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            logger.info(f"Deleted session {session_id}")

    def cleanup_old_sessions(self, days: int = 7):
        """
        Remove sessions older than specified days

        Args:
            days: Number of days to keep sessions

        Returns:
            Number of sessions deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE updated_at < ?",
                (cutoff_date,)
            )
            deleted = cursor.rowcount
            conn.commit()

            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old sessions (older than {days} days)")

            return deleted

    def get_all_sessions(self) -> list:
        """
        Get list of all active sessions

        Returns:
            List of session IDs with metadata
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT session_id, last_agent, created_at, updated_at
                FROM sessions
                ORDER BY updated_at DESC
            """)

            sessions = []
            for row in cursor:
                sessions.append({
                    'session_id': row['session_id'],
                    'last_agent': row['last_agent'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })

            return sessions

    def get_stats(self) -> Dict[str, Any]:
        """
        Get session statistics

        Returns:
            Dictionary with session stats
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    COUNT(DISTINCT last_agent) as unique_agents,
                    MAX(updated_at) as last_activity
                FROM sessions
            """)

            row = cursor.fetchone()

            return {
                'total_sessions': row[0],
                'unique_agents': row[1],
                'last_activity': row[2]
            }

    @staticmethod
    def _empty_session() -> Dict[str, Any]:
        """Create empty session structure"""
        return {
            'last_agent': None,
            'last_query': None,
            'context': {},
            'sizing_session': {
                'active': False,
                'project_type': None,
                'customer': None,
                'location': None,
                'quantity': None,
                'equipment': [],
                'scope': [],
                'full_description': []
            }
        }


# Global session manager instance
session_manager = None

def get_session_manager(db_path: str = "/var/lib/insa-crm/conversation_sessions.db") -> SessionManager:
    """
    Get or create global session manager instance

    Args:
        db_path: Path to SQLite database

    Returns:
        SessionManager instance
    """
    global session_manager
    if session_manager is None:
        session_manager = SessionManager(db_path)
    return session_manager

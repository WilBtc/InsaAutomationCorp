#!/usr/bin/env python3
"""
Authentication Manager for INSA Voice Assistant
Provides user registration, login, and session management with bcrypt password hashing
"""
import sqlite3
import bcrypt
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AuthManager:
    """
    Manages user authentication and session tokens
    """

    def __init__(self, db_path: str = "/var/lib/insa-crm/conversation_sessions.db"):
        """
        Initialize authentication manager

        Args:
            db_path: Path to SQLite database file (shared with SessionManager)
        """
        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

        logger.info(f"AuthManager initialized with database: {db_path}")

    def _init_db(self):
        """Create users and auth_tokens tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)

            # Authentication tokens table (for session management)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Create indices
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_username
                ON users(username)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_email
                ON users(email)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_token_expiry
                ON auth_tokens(expires_at)
            """)

            conn.commit()
            logger.info("Authentication tables initialized")

    def register_user(self, username: str, email: str, password: str, full_name: str = None) -> Dict[str, Any]:
        """
        Register a new user

        Args:
            username: Unique username
            email: Unique email address (must be @insaing.com)
            password: Plain text password (will be hashed)
            full_name: Optional full name

        Returns:
            Dictionary with success status and user_id or error message
        """
        try:
            # Validate email domain (only @insaing.com allowed)
            if not email.lower().endswith('@insaing.com'):
                logger.warning(f"Registration rejected: Invalid email domain '{email}'")
                return {'success': False, 'error': 'Solo se permiten correos @insaing.com'}

            # Hash password with bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO users (username, email, password_hash, full_name)
                    VALUES (?, ?, ?, ?)
                """, (username, email, password_hash, full_name))

                user_id = cursor.lastrowid
                conn.commit()

                logger.info(f"User registered: {username} (ID: {user_id})")
                return {
                    'success': True,
                    'user_id': user_id,
                    'username': username,
                    'email': email
                }

        except sqlite3.IntegrityError as e:
            error_msg = str(e)
            if 'username' in error_msg:
                logger.warning(f"Registration failed: Username '{username}' already exists")
                return {'success': False, 'error': 'Username already exists'}
            elif 'email' in error_msg:
                logger.warning(f"Registration failed: Email '{email}' already exists")
                return {'success': False, 'error': 'Email already exists'}
            else:
                logger.error(f"Registration failed: {e}")
                return {'success': False, 'error': 'Registration failed'}

    def login(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and create session token

        Args:
            username_or_email: Username or email address
            password: Plain text password

        Returns:
            Dictionary with success status, token, and user info or error message
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Check if input is username or email
                cursor = conn.execute("""
                    SELECT * FROM users
                    WHERE username = ? OR email = ?
                """, (username_or_email, username_or_email))

                user = cursor.fetchone()

                if not user:
                    logger.warning(f"Login failed: User '{username_or_email}' not found")
                    return {'success': False, 'error': 'Invalid username/email or password'}

                # Verify password
                if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    logger.warning(f"Login failed: Invalid password for user '{username_or_email}'")
                    return {'success': False, 'error': 'Invalid username/email or password'}

                # Create session token (valid for 30 days)
                token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(days=30)

                conn.execute("""
                    INSERT INTO auth_tokens (token, user_id, expires_at)
                    VALUES (?, ?, ?)
                """, (token, user['user_id'], expires_at))

                # Update last login
                conn.execute("""
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user['user_id'],))

                conn.commit()

                logger.info(f"Login successful: {user['username']} (ID: {user['user_id']})")
                return {
                    'success': True,
                    'token': token,
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name']
                }

        except Exception as e:
            logger.error(f"Login error: {e}")
            return {'success': False, 'error': 'Login failed'}

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify authentication token and return user info

        Args:
            token: Authentication token

        Returns:
            User info dictionary or None if invalid/expired
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                cursor = conn.execute("""
                    SELECT u.user_id, u.username, u.email, u.full_name, t.expires_at
                    FROM auth_tokens t
                    JOIN users u ON t.user_id = u.user_id
                    WHERE t.token = ?
                """, (token,))

                result = cursor.fetchone()

                if not result:
                    logger.debug(f"Token verification failed: Token not found")
                    return None

                # Check if token expired
                expires_at = datetime.fromisoformat(result['expires_at'])
                if datetime.now() > expires_at:
                    logger.debug(f"Token verification failed: Token expired")
                    # Delete expired token
                    conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
                    conn.commit()
                    return None

                return {
                    'user_id': result['user_id'],
                    'username': result['username'],
                    'email': result['email'],
                    'full_name': result['full_name']
                }

        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    def logout(self, token: str) -> bool:
        """
        Logout user by deleting token

        Args:
            token: Authentication token

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
                conn.commit()
                logger.info(f"Logout successful")
                return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired authentication tokens

        Returns:
            Number of tokens deleted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM auth_tokens
                    WHERE expires_at < CURRENT_TIMESTAMP
                """)
                deleted = cursor.rowcount
                conn.commit()

                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} expired tokens")

                return deleted
        except Exception as e:
            logger.error(f"Token cleanup error: {e}")
            return 0

    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information by user_id

        Args:
            user_id: User ID

        Returns:
            User info dictionary or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT user_id, username, email, full_name, created_at, last_login
                    FROM users
                    WHERE user_id = ?
                """, (user_id,))

                user = cursor.fetchone()

                if user:
                    return dict(user)
                return None

        except Exception as e:
            logger.error(f"Get user info error: {e}")
            return None


# Global auth manager instance
auth_manager = None

def get_auth_manager(db_path: str = "/var/lib/insa-crm/conversation_sessions.db") -> AuthManager:
    """
    Get or create global auth manager instance

    Args:
        db_path: Path to SQLite database

    Returns:
        AuthManager instance
    """
    global auth_manager
    if auth_manager is None:
        auth_manager = AuthManager(db_path)
    return auth_manager

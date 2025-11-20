"""
WebSocket Server for Real-Time Telemetry Streaming.

This module implements a production-ready WebSocket server with:
- JWT authentication
- Room-based subscriptions (per well_id)
- Connection management and monitoring
- Heartbeat/ping-pong for connection health
- Rate limiting per client
- Redis pub/sub for multi-instance support
- Comprehensive error handling and logging
"""

import time
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime
from collections import defaultdict
from threading import Lock

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import redis

from app.core import get_logger, get_config
from app.core.auth import decode_jwt_token
from app.core.metrics import (
    websocket_connections,
    websocket_messages,
    websocket_errors,
    websocket_subscriptions
)


logger = get_logger(__name__)
config = get_config()

# Initialize SocketIO with production settings
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="gevent",
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e6,  # 1MB
    always_connect=False
)

# Redis client for pub/sub
redis_client: Optional[redis.Redis] = None

# Connection tracking
class ConnectionManager:
    """Manages WebSocket connections, subscriptions, and rate limiting."""

    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}  # sid -> connection info
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # well_id -> set of sids
        self.message_counts: Dict[str, list] = defaultdict(list)  # sid -> list of timestamps
        self.lock = Lock()

    def add_connection(self, sid: str, user_id: str, username: str) -> None:
        """Add a new connection."""
        with self.lock:
            self.connections[sid] = {
                "user_id": user_id,
                "username": username,
                "connected_at": datetime.utcnow(),
                "last_ping": datetime.utcnow(),
                "message_count": 0,
                "subscriptions": set()
            }
            websocket_connections.labels(status="active").inc()
            logger.info(
                f"WebSocket connection established",
                extra={
                    "extra_fields": {
                        "sid": sid,
                        "user_id": user_id,
                        "username": username,
                        "total_connections": len(self.connections)
                    }
                }
            )

    def remove_connection(self, sid: str) -> None:
        """Remove a connection and clean up subscriptions."""
        with self.lock:
            if sid in self.connections:
                conn_info = self.connections[sid]

                # Remove from all subscriptions
                for well_id in conn_info["subscriptions"]:
                    if sid in self.subscriptions[well_id]:
                        self.subscriptions[well_id].discard(sid)
                        websocket_subscriptions.labels(well_id=well_id).dec()

                        if not self.subscriptions[well_id]:
                            del self.subscriptions[well_id]

                del self.connections[sid]
                websocket_connections.labels(status="active").dec()

                logger.info(
                    f"WebSocket connection closed",
                    extra={
                        "extra_fields": {
                            "sid": sid,
                            "user_id": conn_info["user_id"],
                            "username": conn_info["username"],
                            "duration_seconds": (
                                datetime.utcnow() - conn_info["connected_at"]
                            ).total_seconds(),
                            "message_count": conn_info["message_count"],
                            "total_connections": len(self.connections)
                        }
                    }
                )

    def subscribe(self, sid: str, well_id: str) -> bool:
        """Subscribe a connection to a well's updates."""
        with self.lock:
            if sid not in self.connections:
                return False

            self.connections[sid]["subscriptions"].add(well_id)
            self.subscriptions[well_id].add(sid)
            websocket_subscriptions.labels(well_id=well_id).inc()

            logger.info(
                f"Client subscribed to well updates",
                extra={
                    "extra_fields": {
                        "sid": sid,
                        "well_id": well_id,
                        "user_id": self.connections[sid]["user_id"],
                        "total_subscriptions": len(self.connections[sid]["subscriptions"])
                    }
                }
            )
            return True

    def unsubscribe(self, sid: str, well_id: str) -> bool:
        """Unsubscribe a connection from a well's updates."""
        with self.lock:
            if sid not in self.connections:
                return False

            if well_id in self.connections[sid]["subscriptions"]:
                self.connections[sid]["subscriptions"].discard(well_id)
                self.subscriptions[well_id].discard(sid)
                websocket_subscriptions.labels(well_id=well_id).dec()

                if not self.subscriptions[well_id]:
                    del self.subscriptions[well_id]

                logger.info(
                    f"Client unsubscribed from well updates",
                    extra={
                        "extra_fields": {
                            "sid": sid,
                            "well_id": well_id,
                            "user_id": self.connections[sid]["user_id"]
                        }
                    }
                )
            return True

    def check_rate_limit(self, sid: str, max_messages: int = 10, window_seconds: int = 1) -> bool:
        """
        Check if a connection has exceeded rate limit.

        Args:
            sid: Session ID
            max_messages: Maximum messages allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if within rate limit, False if exceeded
        """
        now = time.time()
        cutoff = now - window_seconds

        with self.lock:
            # Remove old timestamps
            self.message_counts[sid] = [
                ts for ts in self.message_counts[sid] if ts > cutoff
            ]

            # Check limit
            if len(self.message_counts[sid]) >= max_messages:
                return False

            # Add current timestamp
            self.message_counts[sid].append(now)
            return True

    def update_ping(self, sid: str) -> None:
        """Update last ping time for a connection."""
        with self.lock:
            if sid in self.connections:
                self.connections[sid]["last_ping"] = datetime.utcnow()

    def increment_message_count(self, sid: str) -> None:
        """Increment message count for a connection."""
        with self.lock:
            if sid in self.connections:
                self.connections[sid]["message_count"] += 1

    def get_connection_info(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get connection info."""
        with self.lock:
            return self.connections.get(sid)

    def get_subscribers(self, well_id: str) -> Set[str]:
        """Get all subscribers for a well."""
        with self.lock:
            return self.subscriptions.get(well_id, set()).copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        with self.lock:
            return {
                "total_connections": len(self.connections),
                "total_subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
                "unique_wells": len(self.subscriptions),
                "connections": [
                    {
                        "sid": sid[:8] + "...",
                        "user_id": info["user_id"],
                        "username": info["username"],
                        "connected_at": info["connected_at"].isoformat(),
                        "message_count": info["message_count"],
                        "subscriptions": list(info["subscriptions"])
                    }
                    for sid, info in self.connections.items()
                ]
            }


# Global connection manager
connection_manager = ConnectionManager()


def init_socketio(app) -> SocketIO:
    """
    Initialize SocketIO with Flask app.

    Args:
        app: Flask application instance

    Returns:
        Configured SocketIO instance
    """
    global redis_client

    # Initialize Redis client for pub/sub
    try:
        redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True
        )
        redis_client.ping()
        logger.info(
            "Redis connection established for WebSocket pub/sub",
            extra={
                "extra_fields": {
                    "host": config.redis_host,
                    "port": config.redis_port
                }
            }
        )
    except Exception as e:
        logger.warning(
            f"Redis connection failed, WebSocket will run in single-instance mode: {e}",
            extra={"extra_fields": {"error": str(e)}}
        )
        redis_client = None

    # Initialize SocketIO with app
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="gevent"
    )

    logger.info("SocketIO initialized with Flask app")
    return socketio


def authenticate_websocket(auth_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Authenticate WebSocket connection using JWT token.

    Args:
        auth_data: Authentication data containing token

    Returns:
        User data if authenticated, None otherwise
    """
    try:
        token = auth_data.get("token")
        if not token:
            logger.warning("WebSocket authentication failed: No token provided")
            return None

        # Decode and verify JWT token
        payload = decode_jwt_token(token)
        if not payload:
            logger.warning("WebSocket authentication failed: Invalid token")
            return None

        return {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "role": payload.get("role")
        }
    except Exception as e:
        logger.error(
            f"WebSocket authentication error: {e}",
            exc_info=e
        )
        return None


# ============================================================================
# WebSocket Event Handlers
# ============================================================================

@socketio.on("connect")
def handle_connect(auth: Dict[str, Any]) -> bool:
    """
    Handle client connection.

    Args:
        auth: Authentication data

    Returns:
        True if connection accepted, False to reject
    """
    try:
        # Authenticate connection
        user_data = authenticate_websocket(auth)
        if not user_data:
            logger.warning(
                "WebSocket connection rejected: Authentication failed",
                extra={
                    "extra_fields": {
                        "sid": request.sid,
                        "remote_addr": request.remote_addr
                    }
                }
            )
            return False

        # Add connection
        connection_manager.add_connection(
            request.sid,
            user_data["user_id"],
            user_data["username"]
        )

        # Send welcome message
        emit("connected", {
            "message": "Connected to Alkhorayef ESP IoT Platform",
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "timestamp": datetime.utcnow().isoformat()
        })

        return True

    except Exception as e:
        logger.error(
            f"Error handling WebSocket connection: {e}",
            exc_info=e,
            extra={
                "extra_fields": {
                    "sid": request.sid,
                    "remote_addr": request.remote_addr
                }
            }
        )
        websocket_errors.labels(error_type="connection_error").inc()
        return False


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle client disconnection."""
    try:
        connection_manager.remove_connection(request.sid)
    except Exception as e:
        logger.error(
            f"Error handling WebSocket disconnection: {e}",
            exc_info=e,
            extra={"extra_fields": {"sid": request.sid}}
        )
        websocket_errors.labels(error_type="disconnection_error").inc()


@socketio.on("ping")
def handle_ping() -> None:
    """Handle ping from client to maintain connection."""
    try:
        connection_manager.update_ping(request.sid)
        emit("pong", {"timestamp": datetime.utcnow().isoformat()})
    except Exception as e:
        logger.error(
            f"Error handling ping: {e}",
            exc_info=e,
            extra={"extra_fields": {"sid": request.sid}}
        )


@socketio.on("subscribe")
def handle_subscribe(data: Dict[str, Any]) -> None:
    """
    Handle subscription to well updates.

    Args:
        data: Subscription data containing well_id
    """
    try:
        well_id = data.get("well_id")
        if not well_id:
            emit("error", {
                "error": "ValidationError",
                "message": "well_id is required"
            })
            return

        # Check rate limit
        if not connection_manager.check_rate_limit(request.sid):
            emit("error", {
                "error": "RateLimitError",
                "message": "Too many requests. Please slow down."
            })
            websocket_errors.labels(error_type="rate_limit").inc()
            return

        # Subscribe to well
        success = connection_manager.subscribe(request.sid, well_id)
        if success:
            join_room(f"well_{well_id}")
            emit("subscribed", {
                "well_id": well_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            emit("error", {
                "error": "SubscriptionError",
                "message": "Failed to subscribe to well updates"
            })
            websocket_errors.labels(error_type="subscription_error").inc()

    except Exception as e:
        logger.error(
            f"Error handling subscription: {e}",
            exc_info=e,
            extra={
                "extra_fields": {
                    "sid": request.sid,
                    "data": data
                }
            }
        )
        emit("error", {
            "error": "InternalError",
            "message": "An unexpected error occurred"
        })
        websocket_errors.labels(error_type="subscription_error").inc()


@socketio.on("unsubscribe")
def handle_unsubscribe(data: Dict[str, Any]) -> None:
    """
    Handle unsubscription from well updates.

    Args:
        data: Unsubscription data containing well_id
    """
    try:
        well_id = data.get("well_id")
        if not well_id:
            emit("error", {
                "error": "ValidationError",
                "message": "well_id is required"
            })
            return

        # Unsubscribe from well
        success = connection_manager.unsubscribe(request.sid, well_id)
        if success:
            leave_room(f"well_{well_id}")
            emit("unsubscribed", {
                "well_id": well_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            emit("error", {
                "error": "UnsubscriptionError",
                "message": "Failed to unsubscribe from well updates"
            })

    except Exception as e:
        logger.error(
            f"Error handling unsubscription: {e}",
            exc_info=e,
            extra={
                "extra_fields": {
                    "sid": request.sid,
                    "data": data
                }
            }
        )
        emit("error", {
            "error": "InternalError",
            "message": "An unexpected error occurred"
        })


@socketio.on("get_stats")
def handle_get_stats() -> None:
    """Handle request for connection statistics."""
    try:
        conn_info = connection_manager.get_connection_info(request.sid)
        if not conn_info:
            emit("error", {
                "error": "NotFoundError",
                "message": "Connection not found"
            })
            return

        # Only allow admins to see full stats
        if conn_info.get("role") == "admin":
            emit("stats", connection_manager.get_stats())
        else:
            # Regular users only see their own stats
            emit("stats", {
                "connected_at": conn_info["connected_at"].isoformat(),
                "message_count": conn_info["message_count"],
                "subscriptions": list(conn_info["subscriptions"])
            })

    except Exception as e:
        logger.error(
            f"Error getting stats: {e}",
            exc_info=e,
            extra={"extra_fields": {"sid": request.sid}}
        )
        emit("error", {
            "error": "InternalError",
            "message": "An unexpected error occurred"
        })


# ============================================================================
# Message Broadcasting Functions
# ============================================================================

def broadcast_telemetry_update(well_id: str, data: Dict[str, Any]) -> None:
    """
    Broadcast telemetry update to all subscribers of a well.

    Args:
        well_id: Well identifier
        data: Telemetry data to broadcast
    """
    try:
        message = {
            "event": "telemetry_update",
            "timestamp": datetime.utcnow().isoformat(),
            "well_id": well_id,
            "data": data
        }

        # Emit to room (all subscribers)
        socketio.emit(
            "telemetry_update",
            message,
            room=f"well_{well_id}"
        )

        # Track metrics
        subscriber_count = len(connection_manager.get_subscribers(well_id))
        websocket_messages.labels(
            message_type="telemetry_update",
            well_id=well_id
        ).inc(subscriber_count)

        logger.debug(
            f"Broadcasted telemetry update",
            extra={
                "extra_fields": {
                    "well_id": well_id,
                    "subscriber_count": subscriber_count
                }
            }
        )

    except Exception as e:
        logger.error(
            f"Error broadcasting telemetry update: {e}",
            exc_info=e,
            extra={
                "extra_fields": {
                    "well_id": well_id,
                    "data": data
                }
            }
        )
        websocket_errors.labels(error_type="broadcast_error").inc()


def broadcast_alert(well_id: str, alert_data: Dict[str, Any]) -> None:
    """
    Broadcast alert to all subscribers of a well.

    Args:
        well_id: Well identifier
        alert_data: Alert data to broadcast
    """
    try:
        message = {
            "event": "alert",
            "timestamp": datetime.utcnow().isoformat(),
            "well_id": well_id,
            "alert": alert_data
        }

        socketio.emit(
            "alert",
            message,
            room=f"well_{well_id}"
        )

        subscriber_count = len(connection_manager.get_subscribers(well_id))
        websocket_messages.labels(
            message_type="alert",
            well_id=well_id
        ).inc(subscriber_count)

        logger.info(
            f"Broadcasted alert",
            extra={
                "extra_fields": {
                    "well_id": well_id,
                    "alert_type": alert_data.get("type"),
                    "subscriber_count": subscriber_count
                }
            }
        )

    except Exception as e:
        logger.error(
            f"Error broadcasting alert: {e}",
            exc_info=e,
            extra={
                "extra_fields": {
                    "well_id": well_id,
                    "alert_data": alert_data
                }
            }
        )
        websocket_errors.labels(error_type="broadcast_error").inc()

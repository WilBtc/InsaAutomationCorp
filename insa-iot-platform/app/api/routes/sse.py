"""
Server-Sent Events (SSE) endpoint for real-time telemetry streaming.

This module provides SSE support for browsers that don't support WebSockets
or for clients that prefer a simpler HTTP-based streaming protocol.

SSE Features:
- JWT authentication via query parameter
- Auto-reconnect support with Last-Event-ID
- Keep-alive mechanism (heartbeat)
- Room-based subscriptions (per well_id)
- Graceful disconnection handling
"""

import time
import json
import queue
from typing import Dict, Any, Generator, Optional
from datetime import datetime
from threading import Thread, Event

from flask import Blueprint, request, Response, stream_with_context
import redis

from app.core import get_logger, get_config, ValidationError
from app.core.auth import decode_jwt_token
from app.core.metrics import (
    sse_connections,
    sse_messages,
    sse_errors
)


logger = get_logger(__name__)
config = get_config()

sse_bp = Blueprint("sse", __name__, url_prefix="/api/v1/sse")

# Redis client for pub/sub
redis_client: Optional[redis.Redis] = None

# SSE connection tracking
class SSEConnectionManager:
    """Manages SSE connections and subscriptions."""

    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.redis_threads: Dict[str, Thread] = {}

    def add_connection(self, conn_id: str, well_id: str, user_id: str) -> queue.Queue:
        """
        Add a new SSE connection.

        Args:
            conn_id: Connection identifier
            well_id: Well identifier to subscribe to
            user_id: User identifier

        Returns:
            Queue for receiving messages
        """
        msg_queue = queue.Queue(maxsize=100)

        self.connections[conn_id] = {
            "well_id": well_id,
            "user_id": user_id,
            "queue": msg_queue,
            "connected_at": datetime.utcnow(),
            "message_count": 0
        }

        sse_connections.labels(well_id=well_id).inc()

        logger.info(
            f"SSE connection established",
            extra={
                "extra_fields": {
                    "conn_id": conn_id,
                    "well_id": well_id,
                    "user_id": user_id,
                    "total_connections": len(self.connections)
                }
            }
        )

        return msg_queue

    def remove_connection(self, conn_id: str) -> None:
        """Remove an SSE connection."""
        if conn_id in self.connections:
            conn_info = self.connections[conn_id]
            well_id = conn_info["well_id"]

            # Stop Redis listener thread if exists
            if conn_id in self.redis_threads:
                # The thread will stop when the queue is closed
                pass

            del self.connections[conn_id]
            sse_connections.labels(well_id=well_id).dec()

            logger.info(
                f"SSE connection closed",
                extra={
                    "extra_fields": {
                        "conn_id": conn_id,
                        "well_id": well_id,
                        "user_id": conn_info["user_id"],
                        "duration_seconds": (
                            datetime.utcnow() - conn_info["connected_at"]
                        ).total_seconds(),
                        "message_count": conn_info["message_count"],
                        "total_connections": len(self.connections)
                    }
                }
            )

    def increment_message_count(self, conn_id: str) -> None:
        """Increment message count for a connection."""
        if conn_id in self.connections:
            self.connections[conn_id]["message_count"] += 1


# Global SSE connection manager
sse_manager = SSEConnectionManager()


def init_redis_client() -> None:
    """Initialize Redis client for SSE pub/sub."""
    global redis_client

    if redis_client is not None:
        return

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
            "Redis connection established for SSE pub/sub",
            extra={
                "extra_fields": {
                    "host": config.redis_host,
                    "port": config.redis_port
                }
            }
        )
    except Exception as e:
        logger.warning(
            f"Redis connection failed for SSE: {e}",
            extra={"extra_fields": {"error": str(e)}}
        )
        redis_client = None


def format_sse_message(event: str, data: Dict[str, Any], event_id: Optional[str] = None) -> str:
    """
    Format a message as Server-Sent Event.

    Args:
        event: Event type
        data: Event data (will be JSON encoded)
        event_id: Optional event ID for reconnection

    Returns:
        Formatted SSE message string
    """
    message = ""

    if event_id:
        message += f"id: {event_id}\n"

    message += f"event: {event}\n"
    message += f"data: {json.dumps(data)}\n\n"

    return message


def redis_listener(conn_id: str, well_id: str, msg_queue: queue.Queue, stop_event: Event) -> None:
    """
    Listen for Redis pub/sub messages and forward to queue.

    Args:
        conn_id: Connection identifier
        well_id: Well identifier
        msg_queue: Queue to send messages to
        stop_event: Event to signal thread to stop
    """
    try:
        if redis_client is None:
            logger.warning(f"Redis not available for SSE connection {conn_id}")
            return

        pubsub = redis_client.pubsub()
        channel = f"telemetry:{well_id}"
        pubsub.subscribe(channel)

        logger.info(
            f"Redis listener started for SSE connection",
            extra={
                "extra_fields": {
                    "conn_id": conn_id,
                    "well_id": well_id,
                    "channel": channel
                }
            }
        )

        for message in pubsub.listen():
            if stop_event.is_set():
                break

            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    msg_queue.put(data, timeout=1)
                except (json.JSONDecodeError, queue.Full) as e:
                    logger.warning(
                        f"Error processing Redis message for SSE: {e}",
                        extra={
                            "extra_fields": {
                                "conn_id": conn_id,
                                "error": str(e)
                            }
                        }
                    )

        pubsub.unsubscribe(channel)
        pubsub.close()

        logger.info(
            f"Redis listener stopped for SSE connection",
            extra={"extra_fields": {"conn_id": conn_id}}
        )

    except Exception as e:
        logger.error(
            f"Redis listener error for SSE connection: {e}",
            exc_info=e,
            extra={"extra_fields": {"conn_id": conn_id}}
        )


def event_stream(
    conn_id: str,
    well_id: str,
    msg_queue: queue.Queue,
    keep_alive_interval: int = 30
) -> Generator[str, None, None]:
    """
    Generate SSE event stream.

    Args:
        conn_id: Connection identifier
        well_id: Well identifier
        msg_queue: Message queue
        keep_alive_interval: Keep-alive interval in seconds

    Yields:
        SSE formatted messages
    """
    stop_event = Event()
    last_keep_alive = time.time()
    message_id = 0

    try:
        # Start Redis listener thread if Redis is available
        if redis_client is not None:
            redis_thread = Thread(
                target=redis_listener,
                args=(conn_id, well_id, msg_queue, stop_event),
                daemon=True
            )
            redis_thread.start()
            sse_manager.redis_threads[conn_id] = redis_thread

        # Send initial connected message
        yield format_sse_message(
            "connected",
            {
                "message": "Connected to Alkhorayef ESP IoT Platform SSE stream",
                "well_id": well_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            event_id=str(message_id)
        )
        message_id += 1

        # Main event loop
        while True:
            current_time = time.time()

            # Send keep-alive if needed
            if current_time - last_keep_alive >= keep_alive_interval:
                yield format_sse_message(
                    "heartbeat",
                    {
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    event_id=str(message_id)
                )
                message_id += 1
                last_keep_alive = current_time

            # Check for messages
            try:
                message = msg_queue.get(timeout=1)

                # Determine event type
                event_type = message.get("event", "telemetry_update")

                # Send message
                yield format_sse_message(
                    event_type,
                    message,
                    event_id=str(message_id)
                )
                message_id += 1

                # Update metrics
                sse_manager.increment_message_count(conn_id)
                sse_messages.labels(
                    message_type=event_type,
                    well_id=well_id
                ).inc()

            except queue.Empty:
                continue

    except GeneratorExit:
        logger.info(
            f"SSE stream closed by client",
            extra={"extra_fields": {"conn_id": conn_id}}
        )

    except Exception as e:
        logger.error(
            f"Error in SSE event stream: {e}",
            exc_info=e,
            extra={"extra_fields": {"conn_id": conn_id}}
        )
        sse_errors.labels(error_type="stream_error").inc()

        # Send error message
        try:
            yield format_sse_message(
                "error",
                {
                    "error": "StreamError",
                    "message": "An error occurred in the event stream"
                },
                event_id=str(message_id)
            )
        except:
            pass

    finally:
        # Cleanup
        stop_event.set()
        sse_manager.remove_connection(conn_id)


@sse_bp.route("/stream/<well_id>", methods=["GET"])
def stream_telemetry(well_id: str) -> Response:
    """
    Stream real-time telemetry updates for a well via SSE.

    Query Parameters:
        token: JWT authentication token (required)
        last_event_id: Last event ID received (for reconnection)

    Args:
        well_id: Well identifier

    Returns:
        SSE event stream
    """
    try:
        # Validate well_id
        if not well_id or not well_id.strip():
            raise ValidationError(
                message="well_id is required",
                field="well_id"
            )

        # Get authentication token from query parameter
        token = request.args.get("token")
        if not token:
            raise ValidationError(
                message="Authentication token is required",
                field="token",
                details={"hint": "Provide token as query parameter: ?token=YOUR_JWT_TOKEN"}
            )

        # Authenticate
        payload = decode_jwt_token(token)
        if not payload:
            sse_errors.labels(error_type="authentication_error").inc()
            return Response(
                format_sse_message(
                    "error",
                    {
                        "error": "AuthenticationError",
                        "message": "Invalid or expired authentication token"
                    }
                ),
                mimetype="text/event-stream",
                status=401
            )

        user_id = payload.get("user_id")
        username = payload.get("username")

        # Get last event ID for reconnection
        last_event_id = request.args.get("last_event_id")
        if last_event_id:
            logger.info(
                f"SSE reconnection detected",
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "user_id": user_id,
                        "last_event_id": last_event_id
                    }
                }
            )

        # Initialize Redis if not already done
        init_redis_client()

        # Create connection ID
        conn_id = f"{user_id}_{well_id}_{int(time.time())}"

        # Create message queue
        msg_queue = sse_manager.add_connection(conn_id, well_id, user_id)

        # Create event stream
        return Response(
            stream_with_context(event_stream(conn_id, well_id, msg_queue)),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Disable Nginx buffering
                "Connection": "keep-alive"
            }
        )

    except ValidationError as e:
        logger.warning(
            f"SSE validation error: {e.message}",
            extra={"extra_fields": e.details}
        )
        sse_errors.labels(error_type="validation_error").inc()
        return Response(
            format_sse_message(
                "error",
                {
                    "error": "ValidationError",
                    "message": e.message,
                    "details": e.details
                }
            ),
            mimetype="text/event-stream",
            status=400
        )

    except Exception as e:
        logger.error(
            f"SSE stream error: {e}",
            exc_info=e,
            extra={
                "extra_fields": {
                    "well_id": well_id
                }
            }
        )
        sse_errors.labels(error_type="internal_error").inc()
        return Response(
            format_sse_message(
                "error",
                {
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred"
                }
            ),
            mimetype="text/event-stream",
            status=500
        )


@sse_bp.route("/health", methods=["GET"])
def sse_health() -> Response:
    """
    SSE health check endpoint.

    Returns:
        JSON response with SSE service health status
    """
    try:
        # Check Redis connection
        redis_healthy = False
        if redis_client is not None:
            try:
                redis_client.ping()
                redis_healthy = True
            except:
                pass

        return {
            "status": "healthy",
            "service": "sse",
            "redis_available": redis_healthy,
            "active_connections": len(sse_manager.connections),
            "timestamp": datetime.utcnow().isoformat()
        }, 200

    except Exception as e:
        logger.error(f"SSE health check error: {e}", exc_info=e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, 500

"""
Real-Time Publisher Service for Telemetry Data.

This service publishes telemetry data to WebSocket and SSE clients in real-time.
It provides:
- Publishing to WebSocket clients via SocketIO
- Publishing to SSE clients via Redis pub/sub
- Rate limiting per client
- Message queuing and batching
- Multi-instance support via Redis
- Comprehensive error handling and logging
"""

import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
from threading import Lock

import redis

from app.core import get_logger, get_config
from app.core.metrics import (
    realtime_publishes,
    realtime_publish_errors,
    realtime_publish_duration
)


logger = get_logger(__name__)
config = get_config()


class RealtimePublisher:
    """
    Publishes telemetry data to real-time clients.

    This service handles publishing telemetry updates to both WebSocket
    and SSE clients, with support for multi-instance deployments via Redis.
    """

    def __init__(self):
        """Initialize the realtime publisher."""
        self.redis_client: Optional[redis.Redis] = None
        self.message_queues: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.rate_limits: Dict[str, List[float]] = defaultdict(list)
        self.lock = Lock()
        self.socketio = None  # Will be set when initializing

        # Initialize Redis connection
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis client for pub/sub."""
        try:
            self.redis_client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            logger.info(
                "Redis connection established for realtime publisher",
                extra={
                    "extra_fields": {
                        "host": config.redis_host,
                        "port": config.redis_port
                    }
                }
            )
        except Exception as e:
            logger.warning(
                f"Redis connection failed for realtime publisher: {e}",
                extra={"extra_fields": {"error": str(e)}}
            )
            self.redis_client = None

    def set_socketio(self, socketio) -> None:
        """
        Set SocketIO instance for WebSocket publishing.

        Args:
            socketio: SocketIO instance
        """
        self.socketio = socketio
        logger.info("SocketIO instance set for realtime publisher")

    def check_rate_limit(
        self,
        client_id: str,
        max_messages: int = 10,
        window_seconds: int = 1
    ) -> bool:
        """
        Check if a client has exceeded rate limit.

        Args:
            client_id: Client identifier
            max_messages: Maximum messages allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if within rate limit, False if exceeded
        """
        now = time.time()
        cutoff = now - window_seconds

        with self.lock:
            # Remove old timestamps
            self.rate_limits[client_id] = [
                ts for ts in self.rate_limits[client_id] if ts > cutoff
            ]

            # Check limit
            if len(self.rate_limits[client_id]) >= max_messages:
                return False

            # Add current timestamp
            self.rate_limits[client_id].append(now)
            return True

    def publish_telemetry_update(
        self,
        well_id: str,
        telemetry_data: Dict[str, Any],
        publish_to_websocket: bool = True,
        publish_to_redis: bool = True
    ) -> bool:
        """
        Publish telemetry update to real-time clients.

        Args:
            well_id: Well identifier
            telemetry_data: Telemetry data to publish
            publish_to_websocket: Whether to publish to WebSocket clients
            publish_to_redis: Whether to publish to Redis (for SSE clients)

        Returns:
            True if successfully published, False otherwise
        """
        start_time = time.time()
        success = False

        try:
            # Create message
            message = {
                "event": "telemetry_update",
                "timestamp": datetime.utcnow().isoformat(),
                "well_id": well_id,
                "data": telemetry_data
            }

            # Publish to WebSocket clients
            if publish_to_websocket and self.socketio is not None:
                try:
                    self.socketio.emit(
                        "telemetry_update",
                        message,
                        room=f"well_{well_id}",
                        namespace="/"
                    )
                    logger.debug(
                        f"Published telemetry update to WebSocket",
                        extra={
                            "extra_fields": {
                                "well_id": well_id,
                                "room": f"well_{well_id}"
                            }
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"Error publishing to WebSocket: {e}",
                        exc_info=e,
                        extra={"extra_fields": {"well_id": well_id}}
                    )
                    realtime_publish_errors.labels(
                        publish_type="websocket",
                        error_type="publish_error"
                    ).inc()

            # Publish to Redis for SSE clients
            if publish_to_redis and self.redis_client is not None:
                try:
                    channel = f"telemetry:{well_id}"
                    self.redis_client.publish(
                        channel,
                        json.dumps(message)
                    )
                    logger.debug(
                        f"Published telemetry update to Redis",
                        extra={
                            "extra_fields": {
                                "well_id": well_id,
                                "channel": channel
                            }
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"Error publishing to Redis: {e}",
                        exc_info=e,
                        extra={"extra_fields": {"well_id": well_id}}
                    )
                    realtime_publish_errors.labels(
                        publish_type="redis",
                        error_type="publish_error"
                    ).inc()

            success = True

            # Update metrics
            duration = time.time() - start_time
            realtime_publishes.labels(
                publish_type="telemetry_update",
                well_id=well_id
            ).inc()
            realtime_publish_duration.labels(
                publish_type="telemetry_update"
            ).observe(duration)

        except Exception as e:
            logger.error(
                f"Error publishing telemetry update: {e}",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "data": telemetry_data
                    }
                }
            )
            realtime_publish_errors.labels(
                publish_type="general",
                error_type="unknown_error"
            ).inc()

        return success

    def publish_batch_updates(
        self,
        updates: List[Dict[str, Any]],
        publish_to_websocket: bool = True,
        publish_to_redis: bool = True
    ) -> Dict[str, Any]:
        """
        Publish a batch of telemetry updates.

        Args:
            updates: List of updates, each containing well_id and data
            publish_to_websocket: Whether to publish to WebSocket clients
            publish_to_redis: Whether to publish to Redis (for SSE clients)

        Returns:
            Dictionary with publish results
        """
        start_time = time.time()
        success_count = 0
        error_count = 0

        try:
            for update in updates:
                well_id = update.get("well_id")
                data = update.get("data")

                if not well_id or not data:
                    logger.warning(
                        "Invalid update in batch: missing well_id or data",
                        extra={"extra_fields": {"update": update}}
                    )
                    error_count += 1
                    continue

                success = self.publish_telemetry_update(
                    well_id,
                    data,
                    publish_to_websocket,
                    publish_to_redis
                )

                if success:
                    success_count += 1
                else:
                    error_count += 1

            duration = time.time() - start_time

            logger.info(
                f"Batch publish completed",
                extra={
                    "extra_fields": {
                        "total": len(updates),
                        "success": success_count,
                        "errors": error_count,
                        "duration_ms": duration * 1000
                    }
                }
            )

            return {
                "total": len(updates),
                "success": success_count,
                "errors": error_count,
                "duration_ms": duration * 1000
            }

        except Exception as e:
            logger.error(
                f"Error in batch publish: {e}",
                exc_info=e,
                extra={"extra_fields": {"batch_size": len(updates)}}
            )
            realtime_publish_errors.labels(
                publish_type="batch",
                error_type="batch_error"
            ).inc()

            return {
                "total": len(updates),
                "success": success_count,
                "errors": len(updates) - success_count,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }

    def publish_alert(
        self,
        well_id: str,
        alert_data: Dict[str, Any],
        publish_to_websocket: bool = True,
        publish_to_redis: bool = True
    ) -> bool:
        """
        Publish alert to real-time clients.

        Args:
            well_id: Well identifier
            alert_data: Alert data to publish
            publish_to_websocket: Whether to publish to WebSocket clients
            publish_to_redis: Whether to publish to Redis (for SSE clients)

        Returns:
            True if successfully published, False otherwise
        """
        start_time = time.time()
        success = False

        try:
            # Create message
            message = {
                "event": "alert",
                "timestamp": datetime.utcnow().isoformat(),
                "well_id": well_id,
                "alert": alert_data
            }

            # Publish to WebSocket clients
            if publish_to_websocket and self.socketio is not None:
                try:
                    self.socketio.emit(
                        "alert",
                        message,
                        room=f"well_{well_id}",
                        namespace="/"
                    )
                    logger.info(
                        f"Published alert to WebSocket",
                        extra={
                            "extra_fields": {
                                "well_id": well_id,
                                "alert_type": alert_data.get("type"),
                                "severity": alert_data.get("severity")
                            }
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"Error publishing alert to WebSocket: {e}",
                        exc_info=e,
                        extra={"extra_fields": {"well_id": well_id}}
                    )
                    realtime_publish_errors.labels(
                        publish_type="websocket",
                        error_type="alert_error"
                    ).inc()

            # Publish to Redis for SSE clients
            if publish_to_redis and self.redis_client is not None:
                try:
                    channel = f"telemetry:{well_id}"
                    self.redis_client.publish(
                        channel,
                        json.dumps(message)
                    )
                    logger.info(
                        f"Published alert to Redis",
                        extra={
                            "extra_fields": {
                                "well_id": well_id,
                                "alert_type": alert_data.get("type")
                            }
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"Error publishing alert to Redis: {e}",
                        exc_info=e,
                        extra={"extra_fields": {"well_id": well_id}}
                    )
                    realtime_publish_errors.labels(
                        publish_type="redis",
                        error_type="alert_error"
                    ).inc()

            success = True

            # Update metrics
            duration = time.time() - start_time
            realtime_publishes.labels(
                publish_type="alert",
                well_id=well_id
            ).inc()
            realtime_publish_duration.labels(
                publish_type="alert"
            ).observe(duration)

        except Exception as e:
            logger.error(
                f"Error publishing alert: {e}",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "well_id": well_id,
                        "alert_data": alert_data
                    }
                }
            )
            realtime_publish_errors.labels(
                publish_type="general",
                error_type="unknown_error"
            ).inc()

        return success

    def publish_diagnostic_update(
        self,
        well_id: str,
        diagnostic_data: Dict[str, Any],
        publish_to_websocket: bool = True,
        publish_to_redis: bool = True
    ) -> bool:
        """
        Publish diagnostic update to real-time clients.

        Args:
            well_id: Well identifier
            diagnostic_data: Diagnostic data to publish
            publish_to_websocket: Whether to publish to WebSocket clients
            publish_to_redis: Whether to publish to Redis (for SSE clients)

        Returns:
            True if successfully published, False otherwise
        """
        start_time = time.time()

        try:
            # Create message
            message = {
                "event": "diagnostic_update",
                "timestamp": datetime.utcnow().isoformat(),
                "well_id": well_id,
                "diagnostic": diagnostic_data
            }

            # Publish to WebSocket clients
            if publish_to_websocket and self.socketio is not None:
                self.socketio.emit(
                    "diagnostic_update",
                    message,
                    room=f"well_{well_id}",
                    namespace="/"
                )

            # Publish to Redis for SSE clients
            if publish_to_redis and self.redis_client is not None:
                channel = f"telemetry:{well_id}"
                self.redis_client.publish(
                    channel,
                    json.dumps(message)
                )

            # Update metrics
            duration = time.time() - start_time
            realtime_publishes.labels(
                publish_type="diagnostic_update",
                well_id=well_id
            ).inc()
            realtime_publish_duration.labels(
                publish_type="diagnostic_update"
            ).observe(duration)

            return True

        except Exception as e:
            logger.error(
                f"Error publishing diagnostic update: {e}",
                exc_info=e,
                extra={"extra_fields": {"well_id": well_id}}
            )
            realtime_publish_errors.labels(
                publish_type="diagnostic",
                error_type="publish_error"
            ).inc()
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get publisher statistics.

        Returns:
            Dictionary with publisher stats
        """
        redis_healthy = False
        if self.redis_client is not None:
            try:
                self.redis_client.ping()
                redis_healthy = True
            except:
                pass

        return {
            "redis_connected": redis_healthy,
            "socketio_initialized": self.socketio is not None,
            "active_rate_limits": len(self.rate_limits),
            "message_queues": len(self.message_queues)
        }


# Global realtime publisher instance
_realtime_publisher: Optional[RealtimePublisher] = None


def get_realtime_publisher() -> RealtimePublisher:
    """
    Get the global realtime publisher instance.

    Returns:
        RealtimePublisher instance
    """
    global _realtime_publisher

    if _realtime_publisher is None:
        _realtime_publisher = RealtimePublisher()
        logger.info("Realtime publisher initialized")

    return _realtime_publisher


def init_realtime_publisher(socketio) -> RealtimePublisher:
    """
    Initialize the realtime publisher with SocketIO instance.

    Args:
        socketio: SocketIO instance

    Returns:
        Initialized RealtimePublisher instance
    """
    publisher = get_realtime_publisher()
    publisher.set_socketio(socketio)
    logger.info("Realtime publisher configured with SocketIO")
    return publisher

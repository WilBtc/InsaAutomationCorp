#!/usr/bin/env python3
"""
INSA Advanced IIoT Platform - WebSocket Real-time Updates
Handles real-time communication with dashboards via Socket.IO

Version: 2.0
Date: October 27, 2025
Author: INSA Automation Corp
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request
from flask_jwt_extended import decode_token
from jwt.exceptions import InvalidTokenError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketServer:
    """WebSocket server for real-time updates"""

    def __init__(self, app):
        """Initialize Socket.IO server"""
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='eventlet',
            logger=False,
            engineio_logger=False,
            ping_timeout=60,
            ping_interval=25
        )

        self.authenticated_clients = {}  # {sid: user_email}
        self.device_subscriptions = {}  # {sid: [device_ids]}

        self._register_handlers()
        logger.info("WebSocket server initialized")

    def _register_handlers(self):
        """Register Socket.IO event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info(f"Client connected: {request.sid}")
            emit('connection_response', {
                'status': 'connected',
                'sid': request.sid,
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            sid = request.sid

            # Clean up authentication
            if sid in self.authenticated_clients:
                user = self.authenticated_clients.pop(sid)
                logger.info(f"Client {sid} disconnected (user: {user})")
            else:
                logger.info(f"Client {sid} disconnected")

            # Clean up subscriptions
            if sid in self.device_subscriptions:
                del self.device_subscriptions[sid]

        @self.socketio.on('authenticate')
        def handle_authenticate(data):
            """Authenticate WebSocket connection with JWT token"""
            try:
                token = data.get('token')
                if not token:
                    emit('auth_error', {'error': 'Token required'})
                    return

                # Decode and validate JWT token
                decoded = decode_token(token)
                user_email = decoded.get('sub')

                # Store authenticated client
                self.authenticated_clients[request.sid] = user_email

                logger.info(f"Client {request.sid} authenticated as {user_email}")
                emit('auth_success', {
                    'status': 'authenticated',
                    'user': user_email,
                    'timestamp': datetime.now().isoformat()
                })

            except InvalidTokenError as e:
                logger.warning(f"Authentication failed for {request.sid}: {e}")
                emit('auth_error', {'error': 'Invalid token'})
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                emit('auth_error', {'error': 'Authentication failed'})

        @self.socketio.on('subscribe_device')
        def handle_subscribe_device(data):
            """Subscribe to device updates"""
            # Check authentication
            if request.sid not in self.authenticated_clients:
                emit('error', {'error': 'Not authenticated'})
                return

            device_id = data.get('device_id')
            if not device_id:
                emit('error', {'error': 'device_id required'})
                return

            # Join device room
            join_room(f"device_{device_id}")

            # Track subscription
            if request.sid not in self.device_subscriptions:
                self.device_subscriptions[request.sid] = []
            if device_id not in self.device_subscriptions[request.sid]:
                self.device_subscriptions[request.sid].append(device_id)

            logger.info(f"Client {request.sid} subscribed to device {device_id}")
            emit('subscription_success', {
                'device_id': device_id,
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('unsubscribe_device')
        def handle_unsubscribe_device(data):
            """Unsubscribe from device updates"""
            # Check authentication
            if request.sid not in self.authenticated_clients:
                emit('error', {'error': 'Not authenticated'})
                return

            device_id = data.get('device_id')
            if not device_id:
                emit('error', {'error': 'device_id required'})
                return

            # Leave device room
            leave_room(f"device_{device_id}")

            # Remove from subscription tracking
            if request.sid in self.device_subscriptions:
                if device_id in self.device_subscriptions[request.sid]:
                    self.device_subscriptions[request.sid].remove(device_id)

            logger.info(f"Client {request.sid} unsubscribed from device {device_id}")
            emit('unsubscription_success', {
                'device_id': device_id,
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('subscribe_all_devices')
        def handle_subscribe_all():
            """Subscribe to all device updates"""
            # Check authentication
            if request.sid not in self.authenticated_clients:
                emit('error', {'error': 'Not authenticated'})
                return

            # Join global room
            join_room('all_devices')

            logger.info(f"Client {request.sid} subscribed to all devices")
            emit('subscription_success', {
                'scope': 'all_devices',
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('get_status')
        def handle_get_status():
            """Get WebSocket connection status"""
            sid = request.sid
            is_authenticated = sid in self.authenticated_clients
            subscriptions = self.device_subscriptions.get(sid, [])

            emit('status_response', {
                'sid': sid,
                'authenticated': is_authenticated,
                'user': self.authenticated_clients.get(sid),
                'subscriptions': subscriptions,
                'timestamp': datetime.now().isoformat()
            })

    # Event emitters (called by application)

    def emit_telemetry_update(self, device_id, telemetry, timestamp=None):
        """Emit telemetry update to subscribed clients"""
        try:
            self.socketio.emit(
                'telemetry_update',
                {
                    'device_id': device_id,
                    'telemetry': telemetry,
                    'timestamp': timestamp or datetime.now().isoformat()
                },
                room=f"device_{device_id}"
            )

            # Also emit to 'all_devices' room
            self.socketio.emit(
                'telemetry_update',
                {
                    'device_id': device_id,
                    'telemetry': telemetry,
                    'timestamp': timestamp or datetime.now().isoformat()
                },
                room='all_devices'
            )

            logger.debug(f"Emitted telemetry update for device {device_id}")
        except Exception as e:
            logger.error(f"Error emitting telemetry update: {e}")

    def emit_device_status(self, device_id, status, last_seen=None):
        """Emit device status change"""
        try:
            self.socketio.emit(
                'device_status',
                {
                    'device_id': device_id,
                    'status': status,
                    'last_seen': last_seen or datetime.now().isoformat(),
                    'timestamp': datetime.now().isoformat()
                },
                room=f"device_{device_id}"
            )

            # Also emit to 'all_devices' room
            self.socketio.emit(
                'device_status',
                {
                    'device_id': device_id,
                    'status': status,
                    'last_seen': last_seen or datetime.now().isoformat(),
                    'timestamp': datetime.now().isoformat()
                },
                room='all_devices'
            )

            logger.info(f"Emitted status change for device {device_id}: {status}")
        except Exception as e:
            logger.error(f"Error emitting device status: {e}")

    def emit_alert(self, alert_id, device_id, severity, message, alert_data=None):
        """Emit alert notification"""
        try:
            self.socketio.emit(
                'alert',
                {
                    'alert_id': alert_id,
                    'device_id': device_id,
                    'severity': severity,
                    'message': message,
                    'data': alert_data or {},
                    'timestamp': datetime.now().isoformat()
                },
                room=f"device_{device_id}"
            )

            # Also emit to 'all_devices' room
            self.socketio.emit(
                'alert',
                {
                    'alert_id': alert_id,
                    'device_id': device_id,
                    'severity': severity,
                    'message': message,
                    'data': alert_data or {},
                    'timestamp': datetime.now().isoformat()
                },
                room='all_devices'
            )

            logger.warning(f"Emitted alert for device {device_id}: {severity} - {message}")
        except Exception as e:
            logger.error(f"Error emitting alert: {e}")

    def emit_alert_update(self, alert_id, device_id, status, acknowledged_by=None):
        """Emit alert status update"""
        try:
            self.socketio.emit(
                'alert_update',
                {
                    'alert_id': alert_id,
                    'device_id': device_id,
                    'status': status,
                    'acknowledged_by': acknowledged_by,
                    'timestamp': datetime.now().isoformat()
                },
                room=f"device_{device_id}"
            )

            # Also emit to 'all_devices' room
            self.socketio.emit(
                'alert_update',
                {
                    'alert_id': alert_id,
                    'device_id': device_id,
                    'status': status,
                    'acknowledged_by': acknowledged_by,
                    'timestamp': datetime.now().isoformat()
                },
                room='all_devices'
            )

            logger.info(f"Emitted alert update for device {device_id}: {status}")
        except Exception as e:
            logger.error(f"Error emitting alert update: {e}")

    def get_socketio(self):
        """Get Socket.IO instance for app.run()"""
        return self.socketio

    def get_connection_stats(self):
        """Get connection statistics"""
        return {
            'connected_clients': len(self.authenticated_clients),
            'authenticated_clients': len(self.authenticated_clients),
            'total_subscriptions': sum(len(subs) for subs in self.device_subscriptions.values())
        }

# Global instance (initialized by app)
_websocket_server = None

def get_websocket_server():
    """Get global WebSocket server instance"""
    return _websocket_server

def init_websocket_server(app):
    """Initialize global WebSocket server instance"""
    global _websocket_server
    _websocket_server = WebSocketServer(app)
    return _websocket_server

"""
WebSocket module for real-time data streaming.

This module provides WebSocket support for the Alkhorayef ESP IoT Platform,
enabling real-time telemetry updates to connected clients.
"""

from app.websocket.ws_server import socketio, init_socketio

__all__ = ["socketio", "init_socketio"]

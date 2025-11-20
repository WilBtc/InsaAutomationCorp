#!/usr/bin/env python3
"""
Python WebSocket Client for Alkhorayef ESP IoT Platform.

This example demonstrates how to connect to the platform's WebSocket
server and receive real-time telemetry updates.

Usage:
    python websocket_client.py --server http://localhost:8000 --token YOUR_JWT_TOKEN --well WELL-001

Requirements:
    pip install python-socketio requests
"""

import argparse
import time
import sys
from typing import Dict, Any

import socketio
import requests


class ESPWebSocketClient:
    """WebSocket client for ESP telemetry streaming."""

    def __init__(self, server_url: str, token: str):
        """
        Initialize WebSocket client.

        Args:
            server_url: Server URL (e.g., http://localhost:8000)
            token: JWT authentication token
        """
        self.server_url = server_url
        self.token = token
        self.sio = socketio.Client()
        self.connected = False
        self.subscriptions = set()

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register WebSocket event handlers."""

        @self.sio.on('connect')
        def on_connect():
            """Handle connection event."""
            self.connected = True
            print(f"[✓] Connected to {self.server_url}")

        @self.sio.on('connected')
        def on_connected(data: Dict[str, Any]):
            """Handle welcome message."""
            print(f"[✓] Welcome: {data.get('message')}")
            print(f"[i] User: {data.get('username')} ({data.get('user_id')})")

        @self.sio.on('disconnect')
        def on_disconnect():
            """Handle disconnection event."""
            self.connected = False
            print("[!] Disconnected from server")

        @self.sio.on('pong')
        def on_pong(data: Dict[str, Any]):
            """Handle heartbeat response."""
            print(f"[♥] Heartbeat received")

        @self.sio.on('subscribed')
        def on_subscribed(data: Dict[str, Any]):
            """Handle subscription confirmation."""
            well_id = data.get('well_id')
            self.subscriptions.add(well_id)
            print(f"[✓] Subscribed to {well_id}")

        @self.sio.on('unsubscribed')
        def on_unsubscribed(data: Dict[str, Any]):
            """Handle unsubscription confirmation."""
            well_id = data.get('well_id')
            self.subscriptions.discard(well_id)
            print(f"[i] Unsubscribed from {well_id}")

        @self.sio.on('telemetry_update')
        def on_telemetry_update(data: Dict[str, Any]):
            """Handle telemetry update."""
            well_id = data.get('well_id')
            timestamp = data.get('timestamp')
            telemetry = data.get('data', {})

            print(f"\n[📊] Telemetry Update: {well_id}")
            print(f"    Timestamp:      {timestamp}")
            print(f"    Flow Rate:      {telemetry.get('flow_rate', 0):.2f} bbl/day")
            print(f"    PIP:            {telemetry.get('pip', 0):.2f} psi")
            print(f"    Motor Current:  {telemetry.get('motor_current', 0):.2f} A")
            print(f"    Motor Temp:     {telemetry.get('motor_temp', 0):.2f} °C")
            print(f"    Vibration:      {telemetry.get('vibration', 0):.2f} mm/s")
            print(f"    VSD Frequency:  {telemetry.get('vsd_frequency', 0):.2f} Hz")

        @self.sio.on('alert')
        def on_alert(data: Dict[str, Any]):
            """Handle alert."""
            well_id = data.get('well_id')
            alert = data.get('alert', {})

            print(f"\n[⚠️] ALERT: {well_id}")
            print(f"    Type:      {alert.get('type')}")
            print(f"    Severity:  {alert.get('severity')}")
            print(f"    Message:   {alert.get('message')}")

        @self.sio.on('diagnostic_update')
        def on_diagnostic_update(data: Dict[str, Any]):
            """Handle diagnostic update."""
            well_id = data.get('well_id')
            diagnostic = data.get('diagnostic', {})

            print(f"\n[🔧] Diagnostic Update: {well_id}")
            print(f"    {diagnostic}")

        @self.sio.on('stats')
        def on_stats(data: Dict[str, Any]):
            """Handle statistics."""
            print(f"\n[📈] Statistics:")
            for key, value in data.items():
                print(f"    {key}: {value}")

        @self.sio.on('error')
        def on_error(data: Dict[str, Any]):
            """Handle error."""
            error = data.get('error', 'Unknown')
            message = data.get('message', 'No message')
            print(f"[✗] Error: {error} - {message}")

        @self.sio.on('connect_error')
        def on_connect_error(data):
            """Handle connection error."""
            print(f"[✗] Connection error: {data}")

    def connect(self) -> bool:
        """
        Connect to WebSocket server.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            print(f"[i] Connecting to {self.server_url}...")
            self.sio.connect(
                self.server_url,
                auth={'token': self.token},
                transports=['websocket', 'polling']
            )
            return True
        except Exception as e:
            print(f"[✗] Connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self.connected:
            self.sio.disconnect()
            print("[i] Disconnected")

    def subscribe(self, well_id: str) -> None:
        """
        Subscribe to well updates.

        Args:
            well_id: Well identifier
        """
        if not self.connected:
            print("[✗] Not connected")
            return

        print(f"[i] Subscribing to {well_id}...")
        self.sio.emit('subscribe', {'well_id': well_id})

    def unsubscribe(self, well_id: str) -> None:
        """
        Unsubscribe from well updates.

        Args:
            well_id: Well identifier
        """
        if not self.connected:
            print("[✗] Not connected")
            return

        print(f"[i] Unsubscribing from {well_id}...")
        self.sio.emit('unsubscribe', {'well_id': well_id})

    def ping(self) -> None:
        """Send heartbeat ping."""
        if self.connected:
            self.sio.emit('ping')

    def get_stats(self) -> None:
        """Request connection statistics."""
        if not self.connected:
            print("[✗] Not connected")
            return

        self.sio.emit('get_stats')

    def run(self, wells: list) -> None:
        """
        Run client and maintain connection.

        Args:
            wells: List of well IDs to subscribe to
        """
        if not self.connect():
            return

        try:
            # Wait for connection
            time.sleep(1)

            # Subscribe to wells
            for well_id in wells:
                self.subscribe(well_id)
                time.sleep(0.5)

            print("\n[i] Listening for updates... (Press Ctrl+C to exit)")

            # Keep alive with periodic pings
            while True:
                time.sleep(25)
                self.ping()

        except KeyboardInterrupt:
            print("\n[i] Shutting down...")
        finally:
            self.disconnect()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='WebSocket client for Alkhorayef ESP IoT Platform'
    )
    parser.add_argument(
        '--server',
        default='http://localhost:8000',
        help='Server URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='JWT authentication token'
    )
    parser.add_argument(
        '--well',
        action='append',
        dest='wells',
        required=True,
        help='Well ID to subscribe to (can be specified multiple times)'
    )

    args = parser.parse_args()

    # Create and run client
    client = ESPWebSocketClient(args.server, args.token)
    client.run(args.wells)


if __name__ == '__main__':
    main()

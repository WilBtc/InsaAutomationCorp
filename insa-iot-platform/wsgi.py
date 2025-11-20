#!/usr/bin/env python3
"""
WSGI entry point for the Alkhorayef ESP IoT Platform.

This file provides the WSGI application instance for production servers
like Gunicorn, uWSGI, or mod_wsgi.

Usage:
    # Development (Flask built-in server with SocketIO)
    python wsgi.py

    # Production (Gunicorn with gevent worker for SocketIO support)
    gunicorn -k gevent -w 1 -b 0.0.0.0:8000 wsgi:app

    # Production with multiple workers (SocketIO)
    gunicorn -k gevent -w 4 -b 0.0.0.0:8000 --worker-connections 1000 wsgi:app

Note: When using SocketIO, use gevent worker class and ensure Redis is configured
for multi-worker support.
"""

from app import create_app, get_config
from app.websocket import socketio, init_socketio
from app.services.realtime_publisher import init_realtime_publisher

# Create the Flask application instance
app = create_app()

# Initialize SocketIO with the Flask app
socketio_instance = init_socketio(app)

# Initialize realtime publisher with SocketIO
init_realtime_publisher(socketio_instance)

if __name__ == "__main__":
    # Run using SocketIO's built-in server (development only)
    config = get_config()
    socketio_instance.run(
        app,
        host="0.0.0.0",
        port=config.port,
        debug=config.debug,
        use_reloader=config.debug
    )

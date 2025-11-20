#!/usr/bin/env python3
"""
WSGI entry point for the Alkhorayef ESP IoT Platform.

This file provides the WSGI application instance for production servers
like Gunicorn, uWSGI, or mod_wsgi.

Usage:
    # Development (Flask built-in server)
    python wsgi.py

    # Production (Gunicorn)
    gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app

    # Production with auto-reload
    gunicorn -w 4 -b 0.0.0.0:8000 --reload wsgi:app
"""

from app import create_app, get_config

# Create the WSGI application instance
app = create_app()

if __name__ == "__main__":
    # Run using Flask's built-in server (development only)
    config = get_config()
    app.run(
        host="0.0.0.0",
        port=config.app_port,
        debug=config.debug,
        use_reloader=config.debug
    )

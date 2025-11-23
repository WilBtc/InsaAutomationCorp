#!/usr/bin/env python3
"""
Quick start script for the modular Alkhorayef ESP IoT Platform.

This script provides an easy way to run the Flask application with
proper configuration and error handling.
"""

import sys
import os
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))


def main():
    """Main entry point for running the application."""
    try:
        # Import the Flask app
        from app import create_app, cleanup_resources
        from app.core import get_config

        # Create and configure the app
        app = create_app()
        config = get_config()

        print("=" * 80)
        print(f"Starting {config.app_name} v{config.version}")
        print("=" * 80)
        print(f"Environment: {config.environment}")
        print(f"Host: {config.host}:{config.port}")
        print(f"Debug: {config.debug}")
        print(f"Database: {config.database.host}:{config.database.port}/{config.database.database}")
        print(f"Redis: {config.redis.host}:{config.redis.port}")
        print("=" * 80)
        print()
        print("API Endpoints:")
        print(f"  Health Check:      http://{config.host}:{config.port}/health")
        print(f"  Telemetry API:     http://{config.host}:{config.port}/api/v1/telemetry")
        print(f"  Diagnostics API:   http://{config.host}:{config.port}/api/v1/diagnostics")
        print(f"  API Documentation: http://{config.host}:{config.port}/api/v1/docs")
        print("=" * 80)
        print()

        if config.is_production:
            print("WARNING: Running Flask development server in production is not recommended!")
            print("Use a production WSGI server like gunicorn instead:")
            print(f"  gunicorn -w 4 -b {config.host}:{config.port} app:app")
            print()
            response = input("Continue anyway? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("Aborted.")
                return 1

        # Run the application
        try:
            app.run(
                host=config.host,
                port=config.port,
                debug=config.debug,
                use_reloader=config.debug
            )
        except KeyboardInterrupt:
            print("\n\nShutting down gracefully...")
        finally:
            cleanup_resources()
            print("Shutdown complete.")

        return 0

    except ImportError as e:
        print(f"Error: Failed to import application: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return 1

    except Exception as e:
        print(f"Error: Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

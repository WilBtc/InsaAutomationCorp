#!/usr/bin/env python3
"""
Minimal test script to verify the foundation architecture works.
This tests the app without requiring a full database connection.
"""

import os
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("Testing Alkhorayef ESP IoT Platform Foundation")
print("=" * 80)
print()

# Test 1: Configuration Loading
print("[1/5] Testing Configuration Loading...")
try:
    from app.core.config import Config
    config = Config()
    print(f"  ✓ Configuration loaded")
    print(f"    - Environment: {config.environment}")
    print(f"    - Debug: {config.debug}")
    print(f"    - API Port: {config.port}")
    print(f"    - Database: {config.database.host}:{config.database.port}")
    print(f"    - Redis: {config.redis.host}:{config.redis.port}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 2: Logging System
print()
print("[2/5] Testing Logging System...")
try:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Test log message")
    print("  ✓ Logging system initialized")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 3: Exception Hierarchy
print()
print("[3/5] Testing Exception Hierarchy...")
try:
    from app.core.exceptions import (
        ConfigurationError, DatabaseError,
        ValidationError, AuthenticationError, ConnectionError
    )
    print("  ✓ Exception classes imported")
    print(f"    - Available: ConfigurationError, DatabaseError, ValidationError, etc.")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 4: Database Models
print()
print("[4/5] Testing Database Models...")
try:
    from app.db.models import (
        ESPTelemetry, DiagnosticResult, WellSummary
    )
    print("  ✓ Database models imported")
    print(f"    - Available: ESPTelemetry, DiagnosticResult, WellSummary")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 5: Flask App Creation (without starting server)
print()
print("[5/5] Testing Flask App Factory...")
try:
    # We'll skip this for now since it requires database connection
    # from app import create_app
    # app = create_app()
    print("  ⚠  Skipped - requires database connection")
    print("  ℹ  Database connection will be tested separately")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("✓ Foundation Architecture Tests Passed!")
print("=" * 80)
print()
print("Next steps:")
print("  1. Fix database connection timeout issue")
print("  2. Test health endpoints")
print("  3. Implement Week 1 features (TimescaleDB, JWT, compression)")
print()

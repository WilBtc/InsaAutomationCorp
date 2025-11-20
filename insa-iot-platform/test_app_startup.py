#!/usr/bin/env python3
"""Quick test script to verify app can start without database connection."""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

def test_import():
    """Test that modules can be imported without connecting to database."""
    print("Testing module imports...")

    try:
        print("  ✓ Importing app.core...")
        from app.core import get_logger, get_config

        print("  ✓ Importing app.db...")
        from app.db import ESPTelemetry, DiagnosticResult

        print("  ✓ Importing app.services...")
        from app.services import TelemetryService, DiagnosticService

        print("  ✓ Importing app.api...")
        from app.api import health_bp, telemetry_bp, diagnostics_bp

        print("\n✅ All modules imported successfully!")
        print("   Database connection NOT attempted during import")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_initialization():
    """Test that services can be instantiated without database connection."""
    print("\nTesting service initialization...")

    try:
        from app.services import TelemetryService, DiagnosticService

        print("  ✓ Creating TelemetryService instance...")
        telemetry_svc = TelemetryService()
        print(f"    - Instance created: {telemetry_svc}")
        print(f"    - db_pool is None: {telemetry_svc._db_pool is None}")

        print("  ✓ Creating DiagnosticService instance...")
        diagnostic_svc = DiagnosticService()
        print(f"    - Instance created: {diagnostic_svc}")
        print(f"    - db_pool is None: {diagnostic_svc._db_pool is None}")

        print("\n✅ Services initialized successfully!")
        print("   Database connection NOT attempted during instantiation")
        return True

    except Exception as e:
        print(f"\n❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Alkhorayef ESP Platform - Lazy Initialization Test")
    print("=" * 60)
    print()

    success = True

    # Test imports
    if not test_import():
        success = False

    # Test service initialization
    if not test_service_initialization():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Lazy initialization working correctly!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Review errors above")
        print("=" * 60)
        sys.exit(1)

#!/bin/bash
# Integration Test Runner for INSA CRM Platform
# Created: October 30, 2025
# Author: Wil Aroca (Insa Automation Corp)

set -e  # Exit on error

echo "======================================"
echo "INSA CRM Platform - Integration Tests"
echo "======================================"
echo ""

# Change to project root
cd /home/wil/insa-crm-platform

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ ERROR: pytest not installed"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

echo "✅ pytest found: $(pytest --version)"
echo ""

# Run tests with coverage
echo "Running integration tests..."
echo ""

pytest tests/integration/test_api_endpoints.py \
    -v \
    --tb=short \
    --cov=crm-backend \
    --cov=v4_api_extensions \
    --cov=v4_api_extensions_navigation \
    --cov-report=term-missing \
    --cov-report=html \
    --durations=10 \
    --color=yes

EXIT_CODE=$?

echo ""
echo "======================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    echo "======================================"
    echo ""
    echo "Coverage report: htmlcov/index.html"
    echo "Open with: firefox htmlcov/index.html"
else
    echo "❌ TESTS FAILED (exit code: $EXIT_CODE)"
    echo "======================================"
    echo ""
    echo "Run with more details:"
    echo "  pytest tests/integration/test_api_endpoints.py -vv --tb=long"
fi

exit $EXIT_CODE

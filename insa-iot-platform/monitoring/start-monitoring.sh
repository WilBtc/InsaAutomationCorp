#!/bin/bash
# ============================================================================
# Start Monitoring Stack for Alkhorayef ESP IoT Platform
# ============================================================================

set -e

echo "==================================================================="
echo "  Alkhorayef ESP IoT Platform - Monitoring Stack Startup"
echo "==================================================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed."
    exit 1
fi

echo "Starting monitoring stack..."
echo ""

# Start services
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

if docker ps | grep -q alkhorayef-prometheus; then
    echo "✓ Prometheus is running"
else
    echo "✗ Prometheus is not running"
fi

if docker ps | grep -q alkhorayef-grafana; then
    echo "✓ Grafana is running"
else
    echo "✗ Grafana is not running"
fi

if docker ps | grep -q alkhorayef-alertmanager; then
    echo "✓ AlertManager is running"
else
    echo "✗ AlertManager is not running"
fi

echo ""
echo "==================================================================="
echo "  Monitoring Stack Started Successfully"
echo "==================================================================="
echo ""
echo "Access the following URLs:"
echo ""
echo "  Grafana:      http://localhost:3001"
echo "                Username: admin"
echo "                Password: admin (change after first login)"
echo ""
echo "  Prometheus:   http://localhost:9090"
echo "  AlertManager: http://localhost:9093"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop monitoring:"
echo "  docker-compose down"
echo ""
echo "==================================================================="

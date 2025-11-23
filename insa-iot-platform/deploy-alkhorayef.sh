#!/bin/bash

# Alkhorayef ESP AI RAG System - Deployment Script
# Deploys the complete platform with Docker Compose

set -e

echo "🚀 Alkhorayef ESP AI RAG System - Deployment"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker installation
check_docker() {
    echo "🔍 Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        echo "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi

    echo -e "${GREEN}✅ Docker is installed${NC}"
}

# Check environment files
check_env() {
    echo "🔍 Checking environment configuration..."

    if [ -f ".env.alkhorayef" ]; then
        echo -e "${GREEN}✅ Environment file found${NC}"
        cp .env.alkhorayef .env
    else
        echo -e "${YELLOW}⚠️  Environment file not found, using defaults${NC}"
    fi

    # Load Tailscale configuration if exists
    if [ -f ".env.tailscale" ]; then
        source .env.tailscale
        echo -e "${GREEN}✅ Tailscale configuration loaded${NC}"
    fi
}

# Create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."

    mkdir -p logs
    mkdir -p models
    mkdir -p data
    mkdir -p static
    mkdir -p grafana/provisioning/datasources
    mkdir -p grafana/provisioning/dashboards
    mkdir -p grafana/dashboards
    mkdir -p nginx/certs

    echo -e "${GREEN}✅ Directories created${NC}"
}

# Create database initialization script
create_db_init() {
    echo "🗄️ Creating database initialization script..."

    cat > init-db.sql << 'EOF'
-- Alkhorayef ESP Telemetry Database Initialization
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create telemetry table
CREATE TABLE IF NOT EXISTS esp_telemetry (
    id SERIAL,
    well_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    flow_rate FLOAT,
    pip FLOAT,
    motor_current FLOAT,
    motor_temp FLOAT,
    vibration FLOAT,
    vsd_frequency FLOAT,
    flow_variance FLOAT,
    torque FLOAT,
    gor FLOAT,
    PRIMARY KEY (id, timestamp)
);

-- Convert to hypertable
SELECT create_hypertable('esp_telemetry', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_well_time
ON esp_telemetry(well_id, timestamp DESC);

-- Create diagnostic results table
CREATE TABLE IF NOT EXISTS diagnostic_results (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    diagnosis VARCHAR(100),
    confidence FLOAT,
    severity VARCHAR(20),
    actions JSONB,
    telemetry_snapshot JSONB,
    resolution_time VARCHAR(50)
);

-- Create index for diagnostics
CREATE INDEX IF NOT EXISTS idx_diagnosis_well_time
ON diagnostic_results(well_id, timestamp DESC);

-- Create continuous aggregates for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_hourly
WITH (timescaledb.continuous) AS
SELECT
    well_id,
    time_bucket('1 hour', timestamp) AS hour,
    AVG(flow_rate) as avg_flow_rate,
    AVG(pip) as avg_pip,
    AVG(motor_current) as avg_current,
    AVG(motor_temp) as avg_temp,
    MAX(vibration) as max_vibration
FROM esp_telemetry
GROUP BY well_id, hour
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('telemetry_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create retention policy (keep 30 days of raw data)
SELECT add_retention_policy('esp_telemetry',
    drop_after => INTERVAL '30 days',
    if_not_exists => TRUE
);
EOF

    echo -e "${GREEN}✅ Database initialization script created${NC}"
}

# Create Grafana provisioning
create_grafana_config() {
    echo "📊 Creating Grafana provisioning configuration..."

    # Datasource configuration
    cat > grafana/provisioning/datasources/postgres.yaml << 'EOF'
apiVersion: 1

datasources:
  - name: PostgreSQL-Timescale
    type: postgres
    access: proxy
    url: timescaledb:5432
    database: esp_telemetry
    user: alkhorayef
    secureJsonData:
      password: AlkhorayefESP2025!
    jsonData:
      sslmode: disable
      postgresVersion: 1500
      timescaledb: true
    editable: true
    isDefault: true
EOF

    # Dashboard provider configuration
    cat > grafana/provisioning/dashboards/provider.yaml << 'EOF'
apiVersion: 1

providers:
  - name: 'Alkhorayef ESP'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
EOF

    echo -e "${GREEN}✅ Grafana configuration created${NC}"
}

# Build Docker images
build_images() {
    echo "🏗️ Building Docker images..."

    docker-compose build --no-cache || docker compose build --no-cache

    echo -e "${GREEN}✅ Docker images built${NC}"
}

# Start services
start_services() {
    echo "🚀 Starting services..."

    # Stop any existing services
    docker-compose down || docker compose down || true

    # Start services
    docker-compose up -d || docker compose up -d

    echo -e "${GREEN}✅ Services started${NC}"
}

# Wait for services to be ready
wait_for_services() {
    echo "⏳ Waiting for services to be ready..."

    # Wait for PostgreSQL
    echo -n "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker-compose exec -T timescaledb pg_isready -U alkhorayef &> /dev/null; then
            echo -e " ${GREEN}Ready${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done

    # Wait for Redis
    echo -n "Waiting for Redis..."
    for i in {1..30}; do
        if docker-compose exec -T redis redis-cli ping &> /dev/null; then
            echo -e " ${GREEN}Ready${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done

    # Wait for API
    echo -n "Waiting for API..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            echo -e " ${GREEN}Ready${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
}

# Display service status
show_status() {
    echo ""
    echo "📊 Service Status:"
    echo "=================="

    docker-compose ps || docker compose ps

    echo ""
    echo "🌐 Access URLs:"
    echo "==============="

    if [ ! -z "$TAILSCALE_DOMAIN" ]; then
        echo -e "${GREEN}Tailscale HTTPS:${NC}"
        echo "  Platform: https://$TAILSCALE_DOMAIN"
        echo "  API: https://$TAILSCALE_DOMAIN/api"
        echo "  Grafana: https://$TAILSCALE_DOMAIN/grafana"
        echo ""
    fi

    echo -e "${YELLOW}Local Access:${NC}"
    echo "  Platform: http://localhost:80"
    echo "  API: http://localhost:8000"
    echo "  Grafana: http://localhost:3000"
    echo "  RabbitMQ: http://localhost:15672"
    echo ""
    echo "Default Credentials:"
    echo "  Grafana: admin / GrafanaAlkhorayef2025!"
    echo "  RabbitMQ: alkhorayef / RabbitAlkhorayef2025!"
}

# Main deployment flow
main() {
    echo "Starting deployment process..."
    echo ""

    check_docker
    check_env
    create_directories
    create_db_init
    create_grafana_config
    build_images
    start_services
    wait_for_services
    show_status

    echo ""
    echo -e "${GREEN}✅ Deployment complete!${NC}"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop services: docker-compose down"
    echo "To remove all data: docker-compose down -v"
}

# Run main function
main "$@"
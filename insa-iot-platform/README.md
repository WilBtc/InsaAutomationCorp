# INSA IoT Platform

## Enterprise Industrial IoT Infrastructure

A production-grade Industrial Internet of Things (IIoT) platform designed for real-time telemetry processing, advanced analytics, and operational intelligence in industrial environments.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Technical Stack](#technical-stack)
- [Core Components](#core-components)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Data Pipeline](#data-pipeline)
- [Security](#security)
- [Monitoring & Observability](#monitoring--observability)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Application Layer                              │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   REST API  │  │  WebSocket   │  │   GraphQL    │  │   gRPC      │ │
│  │   Gateway   │  │   Server     │  │   Endpoint   │  │  Services   │ │
│  └─────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                           Processing Layer                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   Stream    │  │    Batch     │  │   Machine    │  │  Knowledge  │ │
│  │ Processing  │  │  Processing  │  │   Learning   │  │    Graph    │ │
│  └─────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                           Data Storage Layer                             │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │TimescaleDB  │  │    Redis     │  │   Neo4j      │  │  S3/MinIO   │ │
│  │(Time Series)│  │   (Cache)    │  │(Graph Store) │  │(Object Store)│ │
│  └─────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                           Edge Computing Layer                           │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │    Edge     │  │   Protocol   │  │    Data      │  │   Local     │ │
│  │   Gateway   │  │   Adapters   │  │  Filtering   │  │   Cache     │ │
│  └─────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
Field Devices → Edge Gateway → Message Queue → Stream Processing → Storage
       ↓              ↓              ↓               ↓              ↓
   [Sensors]    [Validation]   [RabbitMQ]    [Analytics]    [TimescaleDB]
   [PLCs]       [Buffering]    [Kafka]       [ML Models]    [Redis]
   [RTUs]       [Protocol]     [MQTT]        [Alerting]     [Neo4j]
                [Translation]
```

## Technical Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Runtime** | Python | 3.10+ | Primary application runtime |
| **Framework** | FastAPI | 0.104+ | Async REST API framework |
| **Database** | PostgreSQL/TimescaleDB | 15+ | Time-series data storage |
| **Cache** | Redis | 7.0+ | High-performance caching |
| **Queue** | RabbitMQ | 3.12+ | Message broker |
| **Graph DB** | Neo4j | 5.0+ | Relationship data storage |
| **Container** | Docker | 24.0+ | Containerization |
| **Orchestration** | Kubernetes | 1.28+ | Container orchestration |

### Protocol Support

- **Industrial Protocols**
  - Modbus TCP/RTU
  - OPC UA
  - DNP3
  - IEC 61850
  - BACnet

- **IoT Protocols**
  - MQTT 3.1.1/5.0
  - CoAP
  - AMQP
  - WebSocket

## Core Components

### 1. Data Ingestion Service

Handles multi-protocol data collection from field devices:

```python
# Example configuration
INGESTION_CONFIG = {
    "protocols": ["modbus", "mqtt", "opcua"],
    "sampling_rate": 1000,  # ms
    "batch_size": 1000,
    "buffer_size": 10000
}
```

### 2. Stream Processing Engine

Real-time data processing with Apache Kafka/RabbitMQ:

- Window-based aggregations
- Anomaly detection
- Real-time alerting
- Data enrichment

### 3. Time Series Database

TimescaleDB optimized for IoT workloads:

- Automatic partitioning
- Compression policies
- Continuous aggregates
- Data retention policies

### 4. Analytics Engine

Machine learning and statistical analysis:

- Predictive maintenance models
- Anomaly detection algorithms
- Pattern recognition
- Trend analysis

### 5. API Gateway

RESTful and GraphQL APIs for data access:

- Rate limiting
- Authentication/Authorization
- Request routing
- Response caching

## System Requirements

### Minimum Requirements

| Component | Specification |
|-----------|--------------|
| **CPU** | 8 cores |
| **RAM** | 16 GB |
| **Storage** | 100 GB SSD |
| **Network** | 1 Gbps |
| **OS** | Ubuntu 22.04 LTS / RHEL 8+ |

### Recommended Production Requirements

| Component | Specification |
|-----------|--------------|
| **CPU** | 32+ cores |
| **RAM** | 64+ GB |
| **Storage** | 1+ TB NVMe SSD |
| **Network** | 10 Gbps |
| **OS** | Ubuntu 22.04 LTS |

## Installation

### Prerequisites

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Install Python dependencies
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip python3-venv
```

### Quick Start

```bash
# Clone the repository
git clone https://github.com/WilBtc/Insa-iot.git
cd insa-iot-platform

# Create environment file
cp .env.example .env

# Configure your environment variables
nano .env

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Initialize the database
docker-compose exec api python init_db.py

# Access the application
# API: http://localhost:8000
# Documentation: http://localhost:8000/docs
```

### Production Deployment

```bash
# Use production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services as needed
docker-compose up -d --scale worker=5

# Enable SSL/TLS
./scripts/setup-ssl.sh
```

## Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/iot_platform
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Message Queue
RABBITMQ_URL=amqp://user:password@localhost:5672
QUEUE_PREFETCH_COUNT=10

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=3600

# Telemetry
TELEMETRY_BATCH_SIZE=1000
TELEMETRY_FLUSH_INTERVAL=5
```

### Data Retention Policies

```sql
-- Configure TimescaleDB retention
SELECT add_retention_policy('telemetry', INTERVAL '30 days');
SELECT add_retention_policy('events', INTERVAL '90 days');
SELECT add_retention_policy('metrics', INTERVAL '1 year');
```

## API Documentation

### RESTful Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/devices` | List all devices |
| `POST` | `/api/v1/telemetry` | Submit telemetry data |
| `GET` | `/api/v1/telemetry/{device_id}` | Get device telemetry |
| `GET` | `/api/v1/analytics/anomalies` | Get anomaly detections |
| `POST` | `/api/v1/alerts` | Create alert rule |
| `GET` | `/api/v1/health` | System health check |

### WebSocket Endpoints

```javascript
// Real-time telemetry subscription
ws://localhost:8000/ws/telemetry/{device_id}

// Alert notifications
ws://localhost:8000/ws/alerts

// System events
ws://localhost:8000/ws/events
```

### Authentication

```bash
# Obtain JWT token
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/devices
```

## Data Pipeline

### Ingestion Pipeline

```
1. Protocol Adapter receives data
2. Data validation and normalization
3. Message queue publishing
4. Stream processing
5. Storage in TimescaleDB
6. Cache update in Redis
7. Real-time notifications
```

### Processing Pipeline

```python
# Example stream processing
async def process_telemetry(data: dict):
    # Validate
    validated_data = await validate_telemetry(data)

    # Enrich
    enriched_data = await enrich_with_metadata(validated_data)

    # Detect anomalies
    anomalies = await detect_anomalies(enriched_data)

    # Store
    await store_telemetry(enriched_data)

    # Alert if needed
    if anomalies:
        await trigger_alerts(anomalies)
```

## Security

### Security Features

- **Authentication**: JWT-based authentication
- **Authorization**: Role-Based Access Control (RBAC)
- **Encryption**: TLS 1.3 for data in transit
- **Audit Logging**: Comprehensive audit trails
- **Input Validation**: Schema validation for all inputs
- **Rate Limiting**: API rate limiting per client
- **Network Segmentation**: Isolated network zones

### IEC 62443 Compliance

- Security Level 1-3 support
- Zone and conduit model implementation
- Security monitoring and incident response
- Patch management procedures
- Security assessment documentation

## Monitoring & Observability

### Metrics Collection

```yaml
# Prometheus metrics exposed at /metrics
metrics:
  - telemetry_ingestion_rate
  - processing_latency
  - storage_capacity
  - api_request_duration
  - error_rate
```

### Logging

```python
# Structured logging configuration
LOGGING = {
    'version': 1,
    'handlers': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(timestamp)s %(level)s %(name)s %(message)s'
        }
    }
}
```

### Distributed Tracing

OpenTelemetry integration for request tracing:

```python
# Trace configuration
from opentelemetry import trace
tracer = trace.get_tracer(__name__)
```

## Development

### Local Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=app

# Run linting
flake8 app/
black app/ --check
mypy app/
```

### Testing

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Load testing
locust -f tests/load/locustfile.py

# Security testing
bandit -r app/
```

### Code Style

- Follow PEP 8 for Python code
- Use Black for code formatting
- Type hints for all functions
- Docstrings for all modules, classes, and functions

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

Copyright (c) 2025 INSA Automation Corp. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

For technical support and inquiries: support@insaautomation.com
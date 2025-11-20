# INSA IoT Platform vs Alkhorayef ESP - Architecture Plan

## Overview

Two **separate applications** sharing common backend infrastructure:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tailscale Secure Network                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  https://iac1.tailc58ea3.ts.net/insa-iot/                      │
│  └─> INSA IoT UI/UX (Port 9000)                                │
│      - General Industrial IoT Platform                          │
│      - Multi-tenant, multi-protocol                            │
│      - Existing dashboard and features                          │
│                                                                  │
│  https://iac1.tailc58ea3.ts.net/alkhorayef                     │
│  └─> Alkhorayef ESP UI/UX (Port 8095)                          │
│      - Specialized for ESP pump diagnostics                     │
│      - AI/ML-powered decision trees                            │
│      - Graphiti knowledge graph integration                     │
│      - Oil & Gas industry branding                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Shared Backend Infrastructure (Docker)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ TimescaleDB      │  │ Redis Cache      │                    │
│  │ Port: 5440       │  │ Port: 6389       │                    │
│  │ (Time-series DB) │  │ (Shared cache)   │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ RabbitMQ         │  │ Grafana          │                    │
│  │ Port: 5672,15672 │  │ Port: 3000       │                    │
│  │ (Message broker) │  │ (Dashboards)     │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Application Separation

### INSA IoT Platform
- **Directory**: `/home/wil/Insa-iot/`
- **URL**: `https://iac1.tailc58ea3.ts.net/insa-iot/`
- **Port**: 9000
- **Purpose**: General industrial IoT platform
- **Features**:
  - Multi-protocol support (Modbus, OPC UA, MQTT, etc.)
  - Asset tracking
  - Real-time telemetry
  - Existing customer deployments

### Alkhorayef ESP Platform
- **Directory**: `/home/wil/insa-iot-platform/` (alkhorayef-specific)
- **URL**: `https://iac1.tailc58ea3.ts.net/alkhorayef`
- **Ports**:
  - API: 8100 (external) → 8000 (internal)
  - ML Service: 8101 (external) → 8001 (internal)
  - Nginx: 8095
- **Purpose**: ESP pump AI diagnostics for oil & gas
- **Features**:
  - AI-powered decision trees
  - Natural language diagnostics
  - Graphiti knowledge graph
  - ESP-specific telemetry analysis
  - Alkhorayef branding and UI

## Shared Infrastructure

Both applications use:
- **TimescaleDB** (5440) - Time-series data storage
- **Redis** (6389) - Caching layer
- **RabbitMQ** (5672, 15672) - Message queue
- **Grafana** (3000) - Visualization (can have separate dashboards)

## Data Isolation Strategy

### Database Schemas
```sql
-- INSA IoT uses schema: public
-- Alkhorayef uses schema: alkhorayef

CREATE SCHEMA IF NOT EXISTS alkhorayef;

-- Alkhorayef tables
CREATE TABLE alkhorayef.esp_telemetry (...);
CREATE TABLE alkhorayef.diagnostic_results (...);

-- INSA IoT tables
CREATE TABLE public.devices (...);
CREATE TABLE public.telemetry (...);
```

### Redis Namespacing
```
# INSA IoT keys
insa:device:{id}:*
insa:telemetry:{id}:*

# Alkhorayef keys
alkhorayef:telemetry:{well_id}:*
alkhorayef:diagnosis:{well_id}:*
```

## Deployment Status

### Currently Running:
- ✅ TimescaleDB (healthy)
- ✅ Redis (healthy)
- ✅ RabbitMQ (running)
- ✅ Grafana (running)
- ✅ Nginx for Alkhorayef (running)
- ✅ Tailscale HTTPS configured

### Pending:
- ⏳ Alkhorayef API container (rebuilding - DNS issue)
- ⏳ Alkhorayef ML service container (rebuilding)
- ⏳ Tailscale container (optional - using host Tailscale)

## Access URLs

### Production URLs (via Tailscale):
- INSA IoT: `https://iac1.tailc58ea3.ts.net/insa-iot/`
- Alkhorayef: `https://iac1.tailc58ea3.ts.net/alkhorayef`
- Grafana: `https://iac1.tailc58ea3.ts.net:3000` or via nginx proxy
- RabbitMQ Admin: `https://iac1.tailc58ea3.ts.net:15672`

### Local Development URLs:
- Alkhorayef API: `http://localhost:8100`
- Alkhorayef ML: `http://localhost:8101`
- Alkhorayef Nginx: `http://localhost:8095`
- Grafana: `http://localhost:3000`
- RabbitMQ: `http://localhost:15672`

## Next Steps

1. **Fix Docker DNS** - Resolve temporary DNS failure
2. **Complete Build** - Finish Alkhorayef API & ML images
3. **Start Containers** - Launch all Alkhorayef services
4. **Test Separation** - Verify both apps work independently
5. **Configure Grafana** - Set up separate dashboards for each app
6. **Document APIs** - Create API documentation for both platforms

## Notes

- Both applications can scale independently
- Shared infrastructure reduces costs
- Data is logically separated (schemas/namespaces)
- Each has its own branding and UI/UX
- HTTPS automatically handled by Tailscale
- No port conflicts - each app has dedicated ports

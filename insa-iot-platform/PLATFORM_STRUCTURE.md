# INSA IoT Platform Structure

## Platform URLs

### Main Landing Page
**URL**: https://iac1.tailc58ea3.ts.net/insa-iot/

The main INSA IoT platform landing page featuring:
- Platform overview and statistics
- Links to all client-specific platforms
- Platform features showcase
- Professional UI/UX with gradient backgrounds

### Client Platforms

#### 1. Alkhorayef ESP Systems (Oil & Gas)
**URL**: https://iac1.tailc58ea3.ts.net/insa-iot/clients/alkhorayef/

ESP (Electric Submersible Pump) AI diagnostics platform featuring:
- Real-time telemetry monitoring
- AI-powered diagnostics with RAG system
- Active wells tracking
- Grafana dashboards integration

**Status**: ✅ Active

#### 2. Vidrio Andino (Glass Manufacturing)
**URL**: https://iac1.tailc58ea3.ts.net/insa-iot/clients/vidrio-andino/

Glass manufacturing IoT platform featuring:
- Production line monitoring
- Quality control automation
- Energy optimization
- Predictive maintenance

**Status**: 🚧 Under Development (Coming Q1 2025)

## Directory Structure

```
/home/wil/insa-iot-platform/static/
├── index.html                          # Main landing page
└── clients/
    ├── alkhorayef/
    │   └── index.html                  # Alkhorayef ESP platform
    └── vidrio-andino/
        └── index.html                  # Vidrio Andino platform
```

## Technical Stack

- **Web Server**: Python HTTP Server (port 9000)
- **Reverse Proxy**: Tailscale Serve
- **Backend Services**:
  - TimescaleDB (time-series database)
  - Redis (caching & pub/sub)
  - RabbitMQ (message queue)
  - Grafana (dashboards)
  - FastAPI (API service)

## Adding New Client Platforms

To add a new client platform:

1. Create directory: `mkdir -p /home/wil/insa-iot-platform/static/clients/CLIENT_NAME`
2. Create `index.html` in the new directory
3. Update main landing page `/home/wil/insa-iot-platform/static/index.html` to add the new client card
4. Access at: `https://iac1.tailc58ea3.ts.net/insa-iot/clients/CLIENT_NAME/`

## Platform Features

- 🎨 Modern, responsive UI/UX design
- 📊 Real-time data visualization
- 🤖 AI/ML predictive analytics
- 🔐 Enterprise-grade security via Tailscale
- ⚡ Edge computing capabilities
- 📈 Multi-tenant architecture supporting multiple clients

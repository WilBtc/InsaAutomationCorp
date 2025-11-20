# Monitoring Stack for Alkhorayef ESP IoT Platform

This directory contains the complete monitoring infrastructure configuration.

## Quick Start

```bash
# Start monitoring stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop monitoring stack
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Components

- **Prometheus** (port 9090) - Metrics collection and storage
- **Grafana** (port 3001) - Visualization and dashboards
- **AlertManager** (port 9093) - Alert routing and notification
- **Node Exporter** (port 9100) - Host system metrics

## Access URLs

- Grafana: http://localhost:3001 (admin/alkhorayef2025)
- Prometheus: http://localhost:9090
- AlertManager: http://localhost:9093

## Files

- `docker-compose.yml` - Monitoring stack services
- `prometheus.yml` - Prometheus configuration
- `prometheus_rules.yml` - Alert rules
- `alertmanager.yml` - Alert routing configuration
- `grafana_dashboard.json` - Pre-built Grafana dashboard
- `grafana_provisioning/` - Grafana auto-configuration

## Configuration

### For Linux Systems

If running on Linux, update `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'alkhorayef-esp-platform'
    static_configs:
      - targets: ['172.17.0.1:8000']  # Change from host.docker.internal
```

### Email Alerts

Edit `alertmanager.yml` to configure SMTP:

```yaml
global:
  smtp_from: 'alerts@alkhorayef.com'
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'alerts@alkhorayef.com'
  smtp_auth_password: 'your-password'
  smtp_require_tls: true
```

Then uncomment the email receivers in the receivers section.

### Slack Alerts

Edit `alertmanager.yml` and add your Slack webhook URL:

```yaml
receivers:
  - name: 'critical-alerts'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
```

## Troubleshooting

See the main documentation: [docs/MONITORING.md](../docs/MONITORING.md)

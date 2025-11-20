# Monitoring and Observability

This document describes the comprehensive monitoring and alerting system for the Alkhorayef ESP IoT Platform.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Available Metrics](#available-metrics)
- [Setting Up Monitoring](#setting-up-monitoring)
- [Using Grafana Dashboards](#using-grafana-dashboards)
- [Configuring Alerts](#configuring-alerts)
- [Health Check Endpoints](#health-check-endpoints)
- [Troubleshooting](#troubleshooting)

## Overview

The monitoring system provides comprehensive observability into the Alkhorayef ESP IoT Platform through:

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **AlertManager** - Alert routing and notification
- **Custom Metrics** - Application-specific metrics exported via `/health/metrics`

### Key Features

- Real-time application performance monitoring
- Database and TimescaleDB-specific metrics
- System resource monitoring (CPU, memory, disk)
- Telemetry ingestion tracking
- Diagnostic analysis monitoring
- Automated alerting on critical conditions
- Pre-built Grafana dashboards

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Alkhorayef ESP Platform                   │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐  │
│  │   Flask API  │───▶│   Metrics    │──▶│  /health/    │  │
│  │              │    │  Collection  │   │   metrics    │  │
│  └──────────────┘    └──────────────┘   └──────┬───────┘  │
└─────────────────────────────────────────────────┼──────────┘
                                                  │
                                                  ▼
                                          ┌───────────────┐
                                          │  Prometheus   │
                                          │  (Port 9090)  │
                                          └───────┬───────┘
                                                  │
                        ┌─────────────────────────┼─────────────────────┐
                        │                         │                     │
                        ▼                         ▼                     ▼
                ┌───────────────┐        ┌───────────────┐    ┌────────────────┐
                │    Grafana    │        │ AlertManager  │    │  Prometheus    │
                │  (Port 3001)  │        │  (Port 9093)  │    │     Rules      │
                └───────────────┘        └───────┬───────┘    └────────────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │  Notifications  │
                                        │  (Email/Slack)  │
                                        └─────────────────┘
```

## Available Metrics

### HTTP Request Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `http_requests_total` | Counter | Total HTTP requests | method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request duration | method, endpoint |
| `http_requests_in_progress` | Gauge | Requests being processed | method, endpoint |
| `http_request_size_bytes` | Histogram | Request payload size | method, endpoint |
| `http_response_size_bytes` | Histogram | Response payload size | method, endpoint |

### Database Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `db_queries_total` | Counter | Total database queries | operation |
| `db_query_duration_seconds` | Histogram | Query execution time | operation |
| `db_connections_active` | Gauge | Active DB connections | - |
| `db_connection_errors_total` | Counter | Connection errors | - |
| `db_query_errors_total` | Counter | Query errors | operation |

### Telemetry Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `telemetry_ingestion_total` | Counter | Records ingested | well_id, source |
| `telemetry_ingestion_rate` | Gauge | Current ingestion rate | - |
| `telemetry_validation_errors_total` | Counter | Validation errors | error_type |
| `telemetry_processing_duration_seconds` | Histogram | Processing time | - |

### Diagnostic Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `diagnostics_analysis_total` | Counter | Analyses performed | well_id, analysis_type |
| `diagnostics_analysis_duration_seconds` | Histogram | Analysis duration | analysis_type |
| `diagnostics_anomalies_detected_total` | Counter | Anomalies found | well_id, anomaly_type |

### Backup Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `backup_operations_total` | Counter | Backup operations | backup_type, status |
| `backup_duration_seconds` | Histogram | Backup duration | backup_type |
| `backup_size_bytes` | Gauge | Last backup size | backup_type |
| `backup_last_success_timestamp` | Gauge | Last successful backup | backup_type |

### TimescaleDB Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `timescaledb_hypertable_chunks_total` | Gauge | Hypertable chunks | hypertable |
| `timescaledb_compression_ratio` | Gauge | Compression ratio | hypertable |
| `timescaledb_continuous_aggregates_total` | Gauge | Continuous aggregates | - |
| `timescaledb_query_cache_hit_rate` | Gauge | Cache hit rate | - |

### System Resource Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `system_cpu_usage_percent` | Gauge | CPU usage | - |
| `system_memory_usage_percent` | Gauge | Memory usage | - |
| `system_memory_available_bytes` | Gauge | Available memory | - |
| `system_disk_usage_percent` | Gauge | Disk usage | mount_point |
| `system_disk_available_bytes` | Gauge | Available disk space | mount_point |
| `system_network_bytes_sent` | Counter | Network bytes sent | - |
| `system_network_bytes_received` | Counter | Network bytes received | - |

## Setting Up Monitoring

### Prerequisites

- Docker and Docker Compose
- Running Alkhorayef ESP Platform on port 8000

### Quick Start

1. **Start the monitoring stack:**

```bash
cd monitoring
docker-compose up -d
```

2. **Verify services are running:**

```bash
docker-compose ps
```

You should see:
- Prometheus (port 9090)
- Grafana (port 3001)
- AlertManager (port 9093)
- Node Exporter (port 9100)

3. **Access the interfaces:**

- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `admin` (default, change after first login)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

### Configuration

#### Prometheus Configuration

Edit `monitoring/prometheus.yml` to configure scrape targets:

```yaml
scrape_configs:
  - job_name: 'alkhorayef-esp-platform'
    scrape_interval: 10s
    metrics_path: '/health/metrics'
    static_configs:
      - targets: ['host.docker.internal:8000']
```

For Linux systems, replace `host.docker.internal` with `172.17.0.1` (Docker bridge IP).

#### Alert Configuration

Edit `monitoring/alertmanager.yml` to configure notification channels:

```yaml
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'ops-team@alkhorayef.com'
        subject: '[CRITICAL] {{ .GroupLabels.alertname }}'
```

Supported notification channels:
- Email (SMTP)
- Slack
- PagerDuty
- Webhooks

## Using Grafana Dashboards

### Pre-built Dashboard

The system includes a comprehensive dashboard that displays:

1. **Overview Panels**
   - Request rate
   - P95 response time
   - Error rate
   - Active database connections

2. **Request Metrics**
   - Request rate by method
   - Response time percentiles (P50, P95, P99)
   - Requests by status code

3. **Database Metrics**
   - Active connections
   - Query duration by operation
   - Connection and query errors

4. **Telemetry Metrics**
   - Ingestion rate
   - Validation errors
   - Processing duration

5. **System Resources**
   - CPU usage
   - Memory usage
   - Disk usage

6. **TimescaleDB Metrics**
   - Hypertable chunks
   - Compression ratios
   - Continuous aggregates

### Accessing the Dashboard

1. Log in to Grafana at http://localhost:3001
2. Go to **Dashboards** → **Browse**
3. Select **Alkhorayef ESP IoT Platform**

### Creating Custom Dashboards

1. Click **+** → **Dashboard** → **Add new panel**
2. Use PromQL to query metrics:

```promql
# Request rate
rate(http_requests_total[5m])

# P95 response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

## Configuring Alerts

### Alert Rules

Alerts are defined in `monitoring/prometheus_rules.yml`. Example:

```yaml
- alert: HighErrorRate
  expr: |
    (sum(rate(http_requests_total{status=~"5.."}[5m])) /
     sum(rate(http_requests_total[5m]))) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }}"
```

### Pre-configured Alerts

| Alert | Condition | Severity | Duration |
|-------|-----------|----------|----------|
| HighErrorRate | Error rate > 5% | Critical | 5 min |
| SlowResponseTime | P95 > 1s | Warning | 5 min |
| DatabaseConnectionFailure | Any connection error | Critical | 2 min |
| HighMemoryUsage | Memory > 80% | Warning | 5 min |
| CriticalMemoryUsage | Memory > 90% | Critical | 2 min |
| LowDiskSpace | Disk > 85% | Warning | 5 min |
| NoDataIngestion | No telemetry for 1 hour | Warning | 1 hour |
| BackupFailure | Backup failed | Critical | 5 min |

### Testing Alerts

1. Access AlertManager: http://localhost:9093
2. View active alerts
3. Check alert routing
4. Silence alerts if needed

## Health Check Endpoints

### Liveness Probe

**Endpoint:** `GET /health/live`

Checks if the application process is running.

```bash
curl http://localhost:8000/health/live
```

Response:
```json
{
  "status": "alive",
  "timestamp": "2025-11-20T12:00:00Z",
  "service": "alkhorayef-esp-iot-platform"
}
```

### Readiness Probe

**Endpoint:** `GET /health/ready`

Checks if the application is ready to serve traffic.

```bash
curl http://localhost:8000/health/ready
```

Response:
```json
{
  "status": "ready",
  "timestamp": "2025-11-20T12:00:00Z",
  "service": "alkhorayef-esp-iot-platform",
  "version": "1.0.0",
  "environment": "production",
  "dependencies": {
    "database": {
      "status": "healthy",
      "type": "postgresql"
    },
    "timescaledb": {
      "status": "healthy"
    }
  }
}
```

### Startup Probe

**Endpoint:** `GET /health/startup`

Checks if the application has completed initialization.

```bash
curl http://localhost:8000/health/startup
```

### Detailed Health Check

**Endpoint:** `GET /health/detailed`

Comprehensive health check with system metrics.

```bash
curl http://localhost:8000/health/detailed
```

Response includes:
- Database connectivity and version
- TimescaleDB extension status
- Hypertable status and chunk counts
- Continuous aggregates
- System resources (CPU, memory, disk)
- Database metrics

### Prometheus Metrics

**Endpoint:** `GET /health/metrics`

Exports metrics in Prometheus format.

```bash
curl http://localhost:8000/health/metrics
```

## Troubleshooting

### Prometheus Not Scraping Metrics

1. Check Prometheus targets: http://localhost:9090/targets
2. Verify the application is accessible from Prometheus container:

```bash
docker exec alkhorayef-prometheus wget -O- http://host.docker.internal:8000/health/metrics
```

3. On Linux, update `prometheus.yml` to use `172.17.0.1` instead of `host.docker.internal`

### Grafana Dashboard Not Loading

1. Check datasource configuration in Grafana
2. Verify Prometheus is accessible:

```bash
docker exec alkhorayef-grafana wget -O- http://prometheus:9090/api/v1/query?query=up
```

3. Re-import the dashboard from `monitoring/grafana_dashboard.json`

### Alerts Not Firing

1. Check alert rules in Prometheus: http://localhost:9090/alerts
2. Verify AlertManager is receiving alerts: http://localhost:9093
3. Check AlertManager configuration for notification channels

### High Memory Usage by Prometheus

1. Reduce retention time in `docker-compose.yml`:
```yaml
--storage.tsdb.retention.time=7d
```

2. Reduce scrape frequency in `prometheus.yml`:
```yaml
scrape_interval: 30s
```

### No Metrics Appearing

1. Verify the monitoring middleware is enabled in the application
2. Check application logs for errors
3. Test metrics endpoint directly:

```bash
curl http://localhost:8000/health/metrics
```

### Container Resource Issues

Check container resource usage:

```bash
docker stats
```

Adjust resource limits in `docker-compose.yml` if needed.

## Best Practices

1. **Retention Policy**
   - Keep Prometheus data for 30 days (default)
   - Archive critical metrics to long-term storage if needed

2. **Alert Fatigue**
   - Configure appropriate thresholds
   - Use alert grouping and inhibition rules
   - Implement maintenance windows

3. **Dashboard Organization**
   - Create role-specific dashboards
   - Use dashboard folders for organization
   - Document custom panels

4. **Performance**
   - Monitor Prometheus memory usage
   - Use recording rules for complex queries
   - Limit metric cardinality

5. **Security**
   - Change default Grafana password
   - Configure authentication for Prometheus
   - Use TLS for production deployments
   - Restrict network access

## Integration with CI/CD

The monitoring system integrates with your deployment pipeline:

```yaml
# Kubernetes health checks
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5

startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 10
  failureThreshold: 30
```

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [AlertManager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)

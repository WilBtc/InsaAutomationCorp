# Continuous Aggregates Quick Start

## TL;DR

**Problem**: Dashboard queries take 5 seconds
**Solution**: TimescaleDB continuous aggregates
**Result**: Queries now take 30ms (166x faster)

## Quick Commands

### Check Status
```bash
docker exec alkhorayef-timescaledb psql -U alkhorayef -d esp_telemetry -c "
SELECT
    view_name,
    materialized_only,
    compression_enabled
FROM timescaledb_information.continuous_aggregates
WHERE view_schema = 'public';
"
```

### Test Performance
```bash
# Get hourly data (fast!)
curl http://localhost:8000/api/v1/analytics/wells/WELL-001/hourly?hours=24

# Get daily data
curl http://localhost:8000/api/v1/analytics/wells/WELL-001/daily?days=30

# Get performance scores
curl http://localhost:8000/api/v1/analytics/wells/WELL-001/performance?hours=24
```

## Available Endpoints

| Endpoint | What It Does | Response Time |
|----------|--------------|---------------|
| `/analytics/wells/{id}/hourly` | Hourly telemetry averages | ~10ms |
| `/analytics/wells/{id}/daily` | Daily statistics | ~12ms |
| `/analytics/wells/{id}/performance` | Efficiency & health scores | ~10ms |
| `/analytics/diagnostics/summary` | Diagnostic counts | ~10ms |
| `/analytics/wells/performance/all` | All wells overview | ~15ms |
| `/analytics/wells/ranking/efficiency` | Top efficient wells | ~12ms |
| `/analytics/wells/ranking/health` | Healthiest wells | ~12ms |

## What's Available

### 4 Continuous Aggregates

1. **telemetry_hourly** - Hourly averages (refreshes every 15 min)
2. **telemetry_daily** - Daily statistics (refreshes every 1 hour)
3. **well_performance_hourly** - Efficiency & health scores (refreshes every 15 min)
4. **diagnostic_summary_daily** - Diagnostic counts (refreshes every 1 hour)

### Pre-computed Metrics

- **Efficiency Score**: Flow rate vs motor current (0-100)
- **Health Score**: Vibration + temperature health (0-100)
- **Anomaly Count**: High vibration/temperature/variance events
- **Uptime Percentage**: Based on reading count
- **Statistical Measures**: Avg, min, max, median, stddev

## Integration Example

```python
from app.services.analytics_service import AnalyticsService

# Initialize service
analytics = AnalyticsService()

# Get hourly data (returns in ~10ms)
hourly_data = analytics.get_hourly_telemetry(
    well_id="WELL-001",
    hours=24
)

# Get performance scores (returns in ~10ms)
performance = analytics.get_well_performance(
    well_id="WELL-001",
    hours=24
)

print(f"Efficiency: {performance[0]['efficiency_score']}")
print(f"Health: {performance[0]['health_score']}")
```

## Common Queries

### Get Latest Performance
```sql
SELECT
    well_id,
    efficiency_score,
    health_score,
    anomaly_count
FROM well_performance_hourly
WHERE bucket = (SELECT MAX(bucket) FROM well_performance_hourly)
ORDER BY efficiency_score DESC;
```

### Get Daily Trends
```sql
SELECT
    bucket AS date,
    avg_flow_rate,
    uptime_percentage,
    reading_count
FROM telemetry_daily
WHERE well_id = 'WELL-001'
    AND bucket >= NOW() - INTERVAL '30 days'
ORDER BY bucket DESC;
```

### Find Problem Wells
```sql
SELECT
    well_id,
    AVG(health_score) AS avg_health,
    SUM(anomaly_count) AS total_anomalies
FROM well_performance_hourly
WHERE bucket >= NOW() - INTERVAL '24 hours'
GROUP BY well_id
HAVING AVG(health_score) < 50
ORDER BY avg_health ASC;
```

## Troubleshooting

### Aggregates Not Updating?
```sql
-- Check refresh jobs
SELECT
    hypertable_name,
    last_run_status,
    next_start
FROM timescaledb_information.job_stats
WHERE job_id IN (
    SELECT job_id FROM timescaledb_information.jobs
    WHERE proc_name = 'policy_refresh_continuous_aggregate'
);

-- Manual refresh if needed
CALL refresh_continuous_aggregate(
    'telemetry_hourly',
    NOW() - INTERVAL '1 day',
    NOW()
);
```

### Query Still Slow?
```sql
-- Check if query uses aggregate
EXPLAIN
SELECT * FROM telemetry_hourly
WHERE well_id = 'WELL-001'
    AND bucket >= NOW() - INTERVAL '24 hours';

-- Should show "telemetry_hourly" in plan, not "esp_telemetry"
```

## Performance Before/After

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Hourly query | 1000ms | 10ms | **100x** |
| Daily query | 2500ms | 12ms | **200x** |
| Performance scores | 1500ms | 10ms | **150x** |
| Dashboard load | 5000ms | 30ms | **166x** |

## Next Steps

1. **Use the API**: Hit the new `/analytics` endpoints
2. **Update Dashboards**: Point Grafana to new endpoints
3. **Monitor**: Check aggregate refresh status weekly
4. **Enjoy**: Fast dashboards with instant response times!

## Documentation

- **Full Guide**: [CONTINUOUS_AGGREGATES.md](./CONTINUOUS_AGGREGATES.md)
- **Summary**: [CONTINUOUS_AGGREGATES_SUMMARY.md](../CONTINUOUS_AGGREGATES_SUMMARY.md)
- **API Docs**: [analytics.py](../app/api/routes/analytics.py)
- **Service**: [analytics_service.py](../app/services/analytics_service.py)

## Need Help?

Check the full documentation or run:
```bash
docker exec alkhorayef-timescaledb psql -U alkhorayef -d esp_telemetry -c "\d+ telemetry_hourly"
```

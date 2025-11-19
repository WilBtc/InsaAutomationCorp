# Performance & Scaling Guide

## Performance Benchmarks

### System Throughput

The INSA IoT Platform has been tested under various load conditions with the following results:

#### Telemetry Ingestion Performance

| Metric | Value | Conditions |
|--------|-------|------------|
| **Maximum Ingestion Rate** | 1M points/second | 32-core, 128GB RAM |
| **Sustained Ingestion** | 500K points/second | 16-core, 64GB RAM |
| **Per-Device Throughput** | 1000 points/second | Standard configuration |
| **Batch Processing** | 100K points/batch | Optimal batch size |

#### API Response Times

| Endpoint | P50 | P95 | P99 |
|----------|-----|-----|-----|
| Device List | 15ms | 45ms | 100ms |
| Telemetry Submit | 10ms | 25ms | 50ms |
| Telemetry Query (1 hour) | 50ms | 150ms | 300ms |
| Telemetry Query (1 day) | 200ms | 500ms | 1s |
| Analytics API | 100ms | 300ms | 800ms |

#### Database Performance

| Operation | Throughput | Latency |
|-----------|------------|---------|
| Write (single point) | 100K/s | < 1ms |
| Write (batch) | 1M/s | < 5ms |
| Read (recent data) | 50K/s | < 10ms |
| Read (historical) | 10K/s | < 50ms |
| Aggregation Query | 1K/s | < 100ms |

## Scaling Strategies

### Horizontal Scaling

#### Application Layer

```yaml
# Kubernetes deployment scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Database Scaling

**TimescaleDB Configuration:**

```sql
-- Partitioning strategy
SELECT create_hypertable('telemetry', 'timestamp',
  chunk_time_interval => INTERVAL '1 day',
  number_partitions => 8);

-- Compression policy
ALTER TABLE telemetry SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'device_id',
  timescaledb.compress_orderby = 'timestamp DESC'
);

SELECT add_compression_policy('telemetry', INTERVAL '7 days');

-- Continuous aggregates
CREATE MATERIALIZED VIEW telemetry_hourly
WITH (timescaledb.continuous) AS
SELECT
  device_id,
  time_bucket('1 hour', timestamp) AS hour,
  AVG(value) as avg_value,
  MAX(value) as max_value,
  MIN(value) as min_value
FROM telemetry
GROUP BY device_id, hour
WITH NO DATA;

SELECT add_continuous_aggregate_policy('telemetry_hourly',
  start_offset => INTERVAL '3 days',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour');
```

### Vertical Scaling

#### Resource Recommendations by Load

| Devices | Data Points/sec | CPU Cores | RAM | Storage | Network |
|---------|----------------|-----------|------|---------|---------|
| 100 | 10K | 4 | 16GB | 500GB SSD | 1Gbps |
| 1,000 | 100K | 16 | 64GB | 2TB NVMe | 10Gbps |
| 10,000 | 1M | 32 | 128GB | 10TB NVMe | 10Gbps |
| 100,000 | 10M | 64+ | 256GB+ | 50TB+ NVMe | 40Gbps |

## Optimization Techniques

### Caching Strategy

#### Redis Configuration

```conf
# redis.conf optimizations
maxmemory 8gb
maxmemory-policy allkeys-lru
save ""
appendonly no
tcp-backlog 511
tcp-keepalive 300
timeout 0

# Performance tuning
databases 16
hz 100
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
```

#### Cache Layers

```python
# Multi-level caching implementation
class CacheManager:
    def __init__(self):
        self.l1_cache = {}  # In-memory cache
        self.l2_cache = redis.Redis()  # Redis cache
        self.l3_cache = PostgreSQL()  # Database

    async def get_telemetry(self, device_id: str, timestamp: datetime):
        # L1 Cache (< 1ms)
        key = f"{device_id}:{timestamp}"
        if key in self.l1_cache:
            return self.l1_cache[key]

        # L2 Cache (< 5ms)
        data = await self.l2_cache.get(key)
        if data:
            self.l1_cache[key] = data
            return data

        # L3 Database (< 50ms)
        data = await self.l3_cache.query(device_id, timestamp)
        await self.l2_cache.setex(key, 3600, data)
        self.l1_cache[key] = data
        return data
```

### Query Optimization

#### Index Strategy

```sql
-- Essential indexes for performance
CREATE INDEX idx_telemetry_device_time ON telemetry(device_id, timestamp DESC);
CREATE INDEX idx_telemetry_time ON telemetry(timestamp DESC);
CREATE INDEX idx_alerts_device_severity ON alerts(device_id, severity, created_at DESC);
CREATE INDEX idx_devices_site_type ON devices(site_id, device_type, status);

-- Partial indexes for common queries
CREATE INDEX idx_active_alerts ON alerts(device_id, created_at)
WHERE status = 'active';

CREATE INDEX idx_online_devices ON devices(site_id, last_seen)
WHERE status = 'online';
```

#### Query Patterns

```python
# Efficient batch queries
async def get_device_telemetry_batch(device_ids: List[str],
                                    start_time: datetime,
                                    end_time: datetime):
    query = """
    SELECT
        device_id,
        time_bucket('5 minutes', timestamp) AS time,
        AVG(value) as avg_value,
        MAX(value) as max_value,
        MIN(value) as min_value,
        COUNT(*) as sample_count
    FROM telemetry
    WHERE
        device_id = ANY($1)
        AND timestamp >= $2
        AND timestamp < $3
    GROUP BY device_id, time
    ORDER BY device_id, time
    """
    return await db.fetch(query, device_ids, start_time, end_time)
```

### Data Pipeline Optimization

#### Stream Processing

```python
# Optimized stream processing with batching
class TelemetryProcessor:
    def __init__(self):
        self.batch_size = 1000
        self.flush_interval = 5  # seconds
        self.buffer = []
        self.last_flush = time.time()

    async def process(self, data: dict):
        self.buffer.append(data)

        if len(self.buffer) >= self.batch_size or \
           time.time() - self.last_flush > self.flush_interval:
            await self.flush()

    async def flush(self):
        if not self.buffer:
            return

        # Batch processing
        batch = self.buffer[:self.batch_size]
        self.buffer = self.buffer[self.batch_size:]

        # Parallel processing
        tasks = [
            self.validate_batch(batch),
            self.enrich_batch(batch),
            self.detect_anomalies_batch(batch)
        ]
        results = await asyncio.gather(*tasks)

        # Batch insert
        await self.store_batch(batch)
        self.last_flush = time.time()
```

## Load Testing

### Test Scenarios

#### Scenario 1: Steady State Load

```python
# Locust test file
from locust import HttpUser, task, between

class SteadyStateUser(HttpUser):
    wait_time = between(1, 3)

    @task(10)
    def submit_telemetry(self):
        self.client.post("/api/v1/telemetry", json={
            "device_id": f"dev_{random.randint(1, 1000)}",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "flow_rate": random.uniform(1000, 1500),
                "pip": random.uniform(2500, 3000),
                "temperature": random.uniform(60, 80)
            }
        })

    @task(5)
    def query_telemetry(self):
        device_id = f"dev_{random.randint(1, 1000)}"
        self.client.get(f"/api/v1/telemetry/{device_id}")

    @task(1)
    def get_analytics(self):
        self.client.get("/api/v1/analytics/anomalies")
```

#### Scenario 2: Burst Load

```bash
# Artillery configuration for burst testing
config:
  target: "https://api.insaiot.com"
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 120
      arrivalRate: 1000
      name: "Burst load"
    - duration: 60
      arrivalRate: 10
      name: "Cool down"

scenarios:
  - name: "Telemetry Burst"
    flow:
      - post:
          url: "/api/v1/telemetry/batch"
          json:
            device_id: "{{ $randomString() }}"
            data: "{{ telemetryData }}"
```

### Performance Monitoring

#### Key Metrics to Monitor

```yaml
# Prometheus queries for monitoring
- name: Ingestion Rate
  query: rate(telemetry_points_total[5m])

- name: API Latency P95
  query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

- name: Database Connection Pool
  query: pg_stat_database_numbackends / pg_settings_max_connections

- name: Cache Hit Ratio
  query: rate(cache_hits_total[5m]) / rate(cache_requests_total[5m])

- name: Error Rate
  query: rate(http_requests_total{status=~"5.."}[5m])
```

## Capacity Planning

### Resource Estimation Formula

```python
def estimate_resources(num_devices: int,
                      samples_per_second_per_device: float,
                      retention_days: int) -> dict:
    """
    Estimate required resources based on load parameters
    """
    # Data ingestion rate
    total_samples_per_second = num_devices * samples_per_second_per_device

    # Storage requirements (assuming 50 bytes per sample)
    bytes_per_sample = 50
    daily_storage_gb = (total_samples_per_second * 86400 * bytes_per_sample) / 1e9
    total_storage_tb = (daily_storage_gb * retention_days) / 1000

    # CPU requirements (1 core per 10K samples/second)
    cpu_cores = max(4, int(total_samples_per_second / 10000))

    # Memory requirements (1GB per 1K devices + overhead)
    memory_gb = max(16, int(num_devices / 1000) * 1 + 8)

    # Network bandwidth (assuming 100 bytes per sample with overhead)
    bandwidth_mbps = (total_samples_per_second * 100 * 8) / 1e6

    return {
        "cpu_cores": cpu_cores,
        "memory_gb": memory_gb,
        "storage_tb": total_storage_tb,
        "bandwidth_mbps": bandwidth_mbps,
        "daily_growth_gb": daily_storage_gb
    }

# Example calculation
resources = estimate_resources(
    num_devices=5000,
    samples_per_second_per_device=1,
    retention_days=90
)
print(f"Required resources: {resources}")
# Output: {
#   'cpu_cores': 4,
#   'memory_gb': 16,
#   'storage_tb': 1.94,
#   'bandwidth_mbps': 4.0,
#   'daily_growth_gb': 21.6
# }
```

### Growth Planning

| Phase | Timeline | Devices | Data Rate | Infrastructure |
|-------|----------|---------|-----------|----------------|
| Pilot | Month 1-3 | 100 | 10K/s | Single server |
| Production | Month 4-6 | 1,000 | 100K/s | 3-node cluster |
| Scale | Month 7-12 | 10,000 | 1M/s | Multi-region |
| Enterprise | Year 2+ | 100,000+ | 10M+/s | Global distribution |

## Troubleshooting Performance Issues

### Common Bottlenecks

#### 1. Database Connection Pool Exhaustion

**Symptoms:**
- Increasing API latency
- Connection timeout errors
- Database CPU < 50% but slow queries

**Solution:**
```python
# Increase connection pool size
DATABASE_CONFIG = {
    "pool_size": 50,
    "max_overflow": 100,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

#### 2. Memory Pressure

**Symptoms:**
- OOM kills
- Frequent garbage collection
- Degraded performance over time

**Solution:**
```python
# Memory optimization
import gc
import resource

# Set memory limits
resource.setrlimit(resource.RLIMIT_AS, (8 * 1024 * 1024 * 1024, -1))

# Aggressive garbage collection
gc.set_threshold(700, 10, 10)

# Use generators for large datasets
def process_large_dataset():
    for chunk in read_in_chunks(chunk_size=1000):
        yield process_chunk(chunk)
```

#### 3. Slow Queries

**Diagnosis:**
```sql
-- Find slow queries
SELECT
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Solution:**
- Add appropriate indexes
- Optimize query structure
- Use materialized views for complex aggregations
- Implement query result caching

## Best Practices

1. **Monitor Continuously**: Set up comprehensive monitoring before performance issues occur
2. **Load Test Regularly**: Run load tests after each major change
3. **Capacity Planning**: Plan for 2x expected peak load
4. **Optimize Early**: Address performance issues before they become critical
5. **Document Changes**: Keep track of performance-related configuration changes
6. **Review Regularly**: Conduct quarterly performance reviews
7. **Automate Scaling**: Implement auto-scaling for predictable load patterns

## Support

For performance-related issues and optimization consulting:

- **Email**: performance@insaautomation.com
- **Documentation**: https://docs.insaiot.com/performance
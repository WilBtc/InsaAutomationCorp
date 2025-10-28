# Phase 12 Week 2 - Prometheus Metrics Integration Plan

**Status:** In Progress (Created Oct 28, 2025)
**Goal:** Integrate Prometheus metrics into all agent components

## Files to Integrate

### ✅ Completed
1. **prometheus_metrics.py** (720 lines)
   - Core metrics infrastructure
   - 50+ metrics defined
   - Decorators and context managers
   - MetricsServer (port 9091)
   - MetricsCollector helper class

2. **sizing_agent_worker.py** (UPDATED)
   - Added `@track_request_metrics('sizing_agent')` decorator
   - Worker health metrics on init
   - Active request tracking
   - Import prometheus_metrics module

### ⏳ In Progress
3. **crm_agent_worker.py**
   - Add same pattern as sizing_agent_worker.py
   - Track request metrics
   - Track handoffs to/from other agents

4. **orchestrator_agent_optimized.py**
   - Track cache hits/misses
   - Track orchestrator routing decisions
   - Track parallel execution metrics

5. **agent_message_bus.py**
   - Track message throughput
   - Track queue depths
   - Track processing times

6. **orchestrator_cache.py**
   - Already tracks some metrics, verify integration
   - Track evictions by reason (TTL, size limit)

7. **agent_retry.py**
   - Track retry attempts by agent
   - Track success after N retries

8. **circuit_breaker.py**
   - Track state transitions
   - Track time in each state

9. **dead_letter_queue.py**
   - Track DLQ size
   - Track replay attempts/successes

### 🆕 New Files Needed
10. **prometheus_config.yml**
    - Prometheus server configuration
    - Scrape configs for port 9091
    - Alerting rules

11. **grafana_dashboards/**
    - 6 JSON dashboard definitions
    - Request metrics
    - Latency histogram
    - Cache performance
    - Worker health
    - Error rates
    - Database operations

12. **test_prometheus_metrics.py**
    - Unit tests for metrics collection
    - Integration tests for decorator
    - Server startup tests

## Integration Pattern

For each worker/agent, follow this pattern:

```python
# 1. Import at top of file
from prometheus_metrics import (
    metrics,
    track_request_metrics,
    track_message_processing,
    track_database_operation
)

# 2. Initialize worker health on __init__
def __init__(self):
    super().__init__(...)
    metrics.update_worker_health('agent_name', 'agent_type', True)
    metrics.update_active_requests('agent_name', 0)
    metrics.update_worker_queue('agent_name', 0)

# 3. Decorate main processing function
@track_request_metrics('agent_name')
def process_task(self, task, session_id, deps):
    metrics.update_active_requests('agent_name', 1)
    try:
        # ... processing ...
        return result
    finally:
        metrics.update_active_requests('agent_name', 0)

# 4. Track specific operations
def handoff_to_agent(self, to_agent, task, context):
    metrics.record_message_sent(
        from_agent=self.agent_id,
        to_agent=to_agent,
        message_type='handoff'
    )
    # ... handoff logic ...

# 5. Track cache operations (if applicable)
def get_from_cache(self, key):
    result = cache.get(key)
    if result:
        metrics.record_cache_hit('agent_cache')
    else:
        metrics.record_cache_miss('agent_cache')
    return result
```

## Metrics Server Startup

Add to main application startup (crm-backend.py):

```python
from prometheus_metrics import initialize_metrics, start_metrics_server

# On application startup
initialize_metrics(version='1.0.0', environment='production')
start_metrics_server(port=9091)

logger.info("Prometheus metrics available at http://localhost:9091/metrics")
```

## Grafana Dashboard IDs

1. **INSA-Overview** - High-level system status (4x2 grid)
2. **INSA-Requests** - Request rates, success/error by agent
3. **INSA-Latency** - P50, P95, P99 latencies by agent
4. **INSA-Cache** - Hit/miss rates, evictions, size
5. **INSA-Workers** - Health status, active requests, queue depth
6. **INSA-Errors** - Error rates, retry attempts, circuit breaker states
7. **INSA-Database** - Query durations, connection pool, operations/sec

## Prometheus Alert Rules

```yaml
groups:
  - name: insa_crm_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(insa_agent_requests_total{status="error"}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate on {{ $labels.agent_type }}"

      - alert: WorkerUnhealthy
        expr: insa_worker_health_status == 0
        for: 2m
        annotations:
          summary: "Worker {{ $labels.worker_name }} is unhealthy"

      - alert: CircuitBreakerOpen
        expr: insa_circuit_breaker_state == 1
        for: 1m
        annotations:
          summary: "Circuit breaker open for {{ $labels.agent_type }}"

      - alert: DeadLetterQueueGrowing
        expr: delta(insa_dead_letter_queue_size[10m]) > 10
        for: 5m
        annotations:
          summary: "Dead letter queue growing for {{ $labels.agent_type }}"
```

## Next Steps

1. Complete CRM agent worker integration (same as sizing)
2. Add cache metrics to orchestrator_cache.py
3. Add message bus metrics to agent_message_bus.py
4. Integrate retry/circuit breaker metrics (already partially done)
5. Create Prometheus configuration file
6. Create 6 Grafana dashboard JSONs
7. Write comprehensive tests
8. Update crm-backend.py to start metrics server
9. Documentation update
10. Git commit

## Expected Results

After full integration:
- ✅ All agents reporting health status
- ✅ Request latency histograms (P50, P95, P99)
- ✅ Cache hit rates visible (target: 90%+)
- ✅ Error rates tracked by agent
- ✅ Circuit breaker state visible
- ✅ Dead letter queue size monitored
- ✅ Database query performance tracked
- ✅ 6 Grafana dashboards operational

## Timeline

- **Day 1 (Today):** Core metrics infrastructure ✅, worker integration (2/5)
- **Day 2:** Complete worker integration, Prometheus config, 3 dashboards
- **Day 3:** Remaining 3 dashboards, tests, documentation, git commit

**Estimated completion:** October 30, 2025

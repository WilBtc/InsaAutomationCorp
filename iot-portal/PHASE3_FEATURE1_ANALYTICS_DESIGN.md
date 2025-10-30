# Phase 3 Feature 1: Advanced Analytics - Design Document
**INSA Advanced IIoT Platform v2.0**

**Start Date**: October 27, 2025 23:00 UTC
**Estimated Time**: 2-3 days
**Status**: 🔄 IN PROGRESS - Design Phase

---

## 📋 Overview

Advanced Analytics module provides time-series analysis, trend detection, statistical functions, and basic forecasting for IoT telemetry data. All analytics use PostgreSQL window functions and aggregations - no external libraries required.

---

## 🎯 Objectives

### 1. Time-Series Analysis (Feature 1a)
**Goal**: Provide moving averages and rate of change calculations

**Endpoints**:
- `GET /api/v1/analytics/timeseries/{device_id}/{metric}` - Time-series data with analysis
  - Query params: `window` (time window for moving average, default: 5 minutes)
  - Query params: `from` and `to` (time range)
  - Returns: timestamps, values, moving average, rate of change

**SQL Window Functions**:
```sql
-- Moving average (5-point window)
AVG(value) OVER (
    ORDER BY timestamp
    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
) as moving_avg

-- Rate of change (per minute)
(value - LAG(value) OVER (ORDER BY timestamp)) /
EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))) * 60
as rate_per_minute
```

### 2. Trend Detection (Feature 1b)
**Goal**: Identify increasing, decreasing, or stable trends

**Endpoints**:
- `GET /api/v1/analytics/trends/{device_id}/{metric}` - Trend analysis
  - Returns: trend direction (increasing/decreasing/stable), confidence, slope

**Algorithm**:
1. Calculate linear regression slope using least squares
2. Determine significance using standard deviation
3. Classify: increasing (slope > threshold), decreasing (slope < -threshold), stable

**SQL Implementation**:
```sql
-- Linear regression slope
(COUNT(*) * SUM(x * y) - SUM(x) * SUM(y)) /
(COUNT(*) * SUM(x * x) - SUM(x) * SUM(x))
WHERE x = EXTRACT(EPOCH FROM timestamp), y = value
```

### 3. Statistical Functions (Feature 1c)
**Goal**: Provide statistical summaries over time windows

**Endpoints**:
- `GET /api/v1/analytics/statistics/{device_id}/{metric}` - Statistical summary
  - Query params: `from`, `to` (time range)
  - Query params: `window` (aggregation window, default: 1 hour)
  - Returns: mean, median, stddev, min, max, percentiles (25th, 50th, 75th, 95th)

**SQL Aggregations**:
```sql
SELECT
    AVG(value) as mean,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median,
    STDDEV(value) as stddev,
    MIN(value) as min,
    MAX(value) as max,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value) as p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value) as p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95
FROM telemetry
WHERE device_id = $1 AND key = $2
  AND timestamp BETWEEN $3 AND $4
```

### 4. Correlation Analysis (Feature 1d)
**Goal**: Calculate correlation between different metrics

**Endpoints**:
- `GET /api/v1/analytics/correlation/{device_id}` - Correlation matrix
  - Query params: `metrics` (comma-separated list, e.g., "temperature,humidity,pressure")
  - Query params: `from`, `to` (time range)
  - Returns: correlation matrix (Pearson correlation coefficients)

**SQL Implementation**:
```sql
-- Pearson correlation coefficient
(COUNT(*) * SUM(x * y) - SUM(x) * SUM(y)) /
SQRT((COUNT(*) * SUM(x*x) - SUM(x)*SUM(x)) *
     (COUNT(*) * SUM(y*y) - SUM(y)*SUM(y)))
```

**Example Output**:
```json
{
  "correlation_matrix": {
    "temperature": {
      "temperature": 1.0,
      "humidity": -0.65,
      "pressure": 0.42
    },
    "humidity": {
      "temperature": -0.65,
      "humidity": 1.0,
      "pressure": -0.31
    },
    "pressure": {
      "temperature": 0.42,
      "humidity": -0.31,
      "pressure": 1.0
    }
  }
}
```

### 5. Simple Forecasting (Feature 1e)
**Goal**: Predict future values using linear regression

**Endpoints**:
- `GET /api/v1/analytics/forecast/{device_id}/{metric}` - Forecast future values
  - Query params: `from`, `to` (historical data range)
  - Query params: `steps` (number of future points to predict, default: 5)
  - Query params: `interval` (time between predictions, default: 5 minutes)
  - Returns: predicted values with timestamps, confidence intervals

**Algorithm**:
1. Calculate linear regression: y = mx + b
2. Project forward using: y_future = m * x_future + b
3. Calculate confidence interval: ±1.96 * std_error

**SQL Implementation**:
```sql
-- Linear regression coefficients
WITH stats AS (
  SELECT
    COUNT(*) as n,
    AVG(EXTRACT(EPOCH FROM timestamp)) as x_mean,
    AVG(value) as y_mean,
    STDDEV(value) as y_stddev
  FROM telemetry
  WHERE device_id = $1 AND key = $2
    AND timestamp BETWEEN $3 AND $4
),
regression AS (
  SELECT
    (SUM((x - x_mean) * (y - y_mean)) / SUM((x - x_mean) * (x - x_mean))) as slope,
    y_mean - slope * x_mean as intercept
  FROM telemetry, stats
  WHERE device_id = $1 AND key = $2
)
SELECT slope, intercept, y_stddev FROM regression, stats
```

---

## 🔌 API Endpoint Summary

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/analytics/timeseries/{device_id}/{metric}` | GET | Time-series with moving avg | JWT + telemetry:read |
| `/api/v1/analytics/trends/{device_id}/{metric}` | GET | Trend detection | JWT + telemetry:read |
| `/api/v1/analytics/statistics/{device_id}/{metric}` | GET | Statistical summary | JWT + telemetry:read |
| `/api/v1/analytics/correlation/{device_id}` | GET | Correlation matrix | JWT + telemetry:read |
| `/api/v1/analytics/forecast/{device_id}/{metric}` | GET | Forecast future values | JWT + telemetry:read |

**Rate Limits**:
- Time-series: 30 per minute (compute-intensive)
- Trends: 30 per minute
- Statistics: 30 per minute
- Correlation: 20 per minute (very compute-intensive)
- Forecast: 20 per minute

---

## 📊 Data Requirements

### Existing Data (Current State)
- **Telemetry Table**: 9 records
- **Device**: 1 (Temperature Sensor 01)
- **Metrics**: temperature (C/°C), humidity (%), pressure (hPa)
- **Timespan**: ~35 minutes (2025-10-27 16:40 to 17:14)

### Data Needed for Testing
**Recommendation**: Generate synthetic historical data for comprehensive testing

**Script to Generate Test Data**:
```python
import psycopg2
import random
from datetime import datetime, timedelta

# Generate 100 data points over 24 hours
device_id = "3a9ccfce-9773-4c72-b905-6a850e961587"
start_time = datetime.now() - timedelta(hours=24)

for i in range(100):
    timestamp = start_time + timedelta(minutes=i * 14.4)  # 100 points in 24h

    # Temperature: 20-30°C with trend and noise
    temp = 25 + 3 * (i / 100) + random.gauss(0, 1)

    # Humidity: 40-80% inversely correlated with temp
    humidity = 60 - (temp - 25) * 2 + random.gauss(0, 3)

    # Pressure: 1000-1020 hPa with small variations
    pressure = 1010 + 5 * (i / 100) + random.gauss(0, 2)

    # Insert telemetry
    INSERT INTO telemetry (device_id, timestamp, key, value, unit, quality)
    VALUES
      (device_id, timestamp, 'temperature', temp, 'C', 100),
      (device_id, timestamp, 'humidity', humidity, '%', 100),
      (device_id, timestamp, 'pressure', pressure, 'hPa', 100);
```

---

## 🛡️ Security & Performance

### Permission Requirements
- New permission: `telemetry:read` (already exists from Phase 2)
- Analytics endpoints require JWT authentication
- Rate limiting to prevent computational abuse

### Performance Targets
| Operation | Target | Notes |
|-----------|--------|-------|
| Time-series query | <500ms | Window functions on indexed timestamps |
| Trend detection | <300ms | Aggregation with least squares |
| Statistics | <200ms | Single-pass aggregation |
| Correlation | <800ms | Multiple metric joins, most complex |
| Forecast | <400ms | Regression calculation + projection |

### Optimization Strategies
1. **Index on (device_id, key, timestamp)** - Already exists
2. **Limit data ranges** - Enforce max 7 days per query
3. **Cache results** - Use Redis for frequently accessed analytics
4. **Pagination** - Limit result sets to 1000 points max

---

## 📝 Implementation Plan

### Phase 1: Time-Series Analysis (2-3 hours)
1. Add `/api/v1/analytics/timeseries` endpoint
2. Implement moving average window function
3. Add rate of change calculation
4. Test with existing 9 data points
5. Generate synthetic data for better testing

### Phase 2: Trend Detection (1-2 hours)
1. Add `/api/v1/analytics/trends` endpoint
2. Implement linear regression slope calculation
3. Add trend classification logic
4. Test with synthetic trending data

### Phase 3: Statistical Functions (1-2 hours)
1. Add `/api/v1/analytics/statistics` endpoint
2. Implement aggregation functions
3. Add percentile calculations
4. Test with various time windows

### Phase 4: Correlation Analysis (2-3 hours)
1. Add `/api/v1/analytics/correlation` endpoint
2. Implement Pearson correlation calculation
3. Handle multiple metric joins
4. Test with temperature/humidity/pressure data

### Phase 5: Simple Forecasting (2-3 hours)
1. Add `/api/v1/analytics/forecast` endpoint
2. Implement linear regression forecasting
3. Calculate confidence intervals
4. Test prediction accuracy

### Phase 6: Testing & Documentation (1-2 hours)
1. Create integration test script
2. Test all 5 endpoints
3. Document API with Swagger annotations
4. Create usage examples

**Total Estimated Time**: 9-15 hours (1.5-2 days)

---

## 🧪 Testing Strategy

### Unit Tests
- Time-series: Verify moving average calculation
- Trends: Verify slope calculation and classification
- Statistics: Verify aggregation accuracy
- Correlation: Verify coefficient calculation
- Forecast: Verify prediction within confidence interval

### Integration Tests
1. **End-to-End Analytics Pipeline**:
   - Generate 100 synthetic data points
   - Query all 5 analytics endpoints
   - Verify results are reasonable

2. **Performance Testing**:
   - Query with 1000+ data points
   - Verify response times meet targets
   - Check rate limiting enforcement

3. **Regression Testing**:
   - Ensure Phase 2 features still work
   - Verify RBAC permissions apply to analytics

---

## 📚 Documentation Deliverables

1. **Implementation Guide**: `PHASE3_FEATURE1_ANALYTICS_COMPLETE.md`
2. **API Documentation**: Swagger annotations in app_advanced.py
3. **Test Report**: `PHASE3_FEATURE1_TEST_REPORT.md`
4. **Usage Examples**: curl commands and Python snippets

---

## 🔗 Dependencies

### Software Dependencies
- PostgreSQL 14+ (window functions, percentile functions)
- Python 3.10+ (already installed)
- psycopg2 (already installed)
- Flask (already installed)
- Flask-JWT-Extended (already installed)

### Data Dependencies
- Telemetry table with indexed (device_id, key, timestamp)
- At least 10-20 data points per metric for meaningful analytics
- Recommendation: Generate synthetic historical data

---

## 🚀 Success Criteria

1. ✅ 5 analytics endpoints implemented
2. ✅ All SQL queries execute in <1 second
3. ✅ Rate limiting enforced on all endpoints
4. ✅ RBAC permissions applied (telemetry:read)
5. ✅ Swagger documentation updated
6. ✅ Integration tests passing
7. ✅ Performance targets met
8. ✅ Zero regression in Phase 2 features

---

**Next Steps**: Implement Feature 1a (Time-Series Analysis) first

---
*Phase 3 Feature 1: Advanced Analytics - Design Complete* ✅
*Ready to implement Feature 1a: Time-Series Analysis*

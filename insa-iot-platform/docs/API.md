# INSA IoT Platform API Reference

## Overview

The INSA IoT Platform provides a comprehensive REST API for device management, telemetry ingestion, analytics, and system configuration.

## Base URL

```
Production: https://api.insaiot.com
Staging: https://staging-api.insaiot.com
Development: http://localhost:8000
```

## Authentication

### JWT Authentication

All API requests require authentication using JWT tokens.

#### Obtaining a Token

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**

```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "<refresh_token>"
}
```

#### Using the Token

Include the token in the Authorization header:

```http
Authorization: Bearer <your_access_token>
```

### API Key Authentication

For machine-to-machine communication:

```http
X-API-Key: <your_api_key>
```

## Rate Limiting

API requests are rate-limited per client:

- **Standard tier**: 100 requests per minute
- **Premium tier**: 1000 requests per minute
- **Enterprise tier**: Unlimited

Rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Endpoints

### Device Management

#### List Devices

```http
GET /api/v1/devices
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number | 1 |
| `page_size` | integer | Items per page | 50 |
| `site_id` | string | Filter by site | - |
| `device_type` | string | Filter by type | - |
| `status` | string | Filter by status | - |

**Response:**

```json
{
  "total": 245,
  "page": 1,
  "page_size": 50,
  "devices": [
    {
      "id": "dev_123456",
      "name": "ESP Pump Unit 01",
      "type": "esp_pump",
      "site_id": "site_001",
      "status": "online",
      "last_seen": "2025-01-19T10:30:00Z",
      "metadata": {
        "manufacturer": "Baker Hughes",
        "model": "CENTRILIFT",
        "serial_number": "ESP2025001"
      }
    }
  ]
}
```

#### Get Device Details

```http
GET /api/v1/devices/{device_id}
```

**Response:**

```json
{
  "id": "dev_123456",
  "name": "ESP Pump Unit 01",
  "type": "esp_pump",
  "site_id": "site_001",
  "status": "online",
  "configuration": {
    "sampling_rate": 1000,
    "protocol": "modbus",
    "address": "192.168.1.10",
    "port": 502
  },
  "telemetry": {
    "flow_rate": 1250.5,
    "pressure": 2800.0,
    "temperature": 65.3,
    "vibration": 0.05,
    "timestamp": "2025-01-19T10:30:00Z"
  }
}
```

#### Create Device

```http
POST /api/v1/devices
Content-Type: application/json

{
  "name": "New ESP Pump",
  "type": "esp_pump",
  "site_id": "site_001",
  "configuration": {
    "protocol": "modbus",
    "address": "192.168.1.11",
    "port": 502,
    "sampling_rate": 1000
  }
}
```

#### Update Device

```http
PUT /api/v1/devices/{device_id}
Content-Type: application/json

{
  "name": "Updated ESP Pump",
  "configuration": {
    "sampling_rate": 500
  }
}
```

#### Delete Device

```http
DELETE /api/v1/devices/{device_id}
```

### Telemetry

#### Submit Telemetry Data

```http
POST /api/v1/telemetry
Content-Type: application/json

{
  "device_id": "dev_123456",
  "timestamp": "2025-01-19T10:30:00Z",
  "data": {
    "flow_rate": 1250.5,
    "pip": 2800.0,
    "motor_current": 85.2,
    "motor_temp": 65.3,
    "vibration": 0.05,
    "vsd_frequency": 50.0
  }
}
```

#### Batch Telemetry Submit

```http
POST /api/v1/telemetry/batch
Content-Type: application/json

{
  "device_id": "dev_123456",
  "data": [
    {
      "timestamp": "2025-01-19T10:30:00Z",
      "flow_rate": 1250.5,
      "pip": 2800.0
    },
    {
      "timestamp": "2025-01-19T10:31:00Z",
      "flow_rate": 1245.3,
      "pip": 2790.0
    }
  ]
}
```

#### Query Telemetry Data

```http
GET /api/v1/telemetry/{device_id}
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `start_time` | ISO 8601 | Start of time range | 24 hours ago |
| `end_time` | ISO 8601 | End of time range | Now |
| `metrics` | string[] | Specific metrics | All |
| `interval` | string | Aggregation interval | raw |
| `aggregation` | string | Aggregation function | mean |

**Example:**

```http
GET /api/v1/telemetry/dev_123456?start_time=2025-01-19T00:00:00Z&end_time=2025-01-19T12:00:00Z&metrics=flow_rate,pip&interval=1h&aggregation=avg
```

**Response:**

```json
{
  "device_id": "dev_123456",
  "start_time": "2025-01-19T00:00:00Z",
  "end_time": "2025-01-19T12:00:00Z",
  "interval": "1h",
  "data": [
    {
      "timestamp": "2025-01-19T00:00:00Z",
      "flow_rate": 1250.5,
      "pip": 2800.0
    },
    {
      "timestamp": "2025-01-19T01:00:00Z",
      "flow_rate": 1248.2,
      "pip": 2795.5
    }
  ]
}
```

### Analytics

#### Get Anomalies

```http
GET /api/v1/analytics/anomalies
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | string | Filter by device |
| `severity` | string | Filter by severity (low, medium, high, critical) |
| `start_time` | ISO 8601 | Start of time range |
| `end_time` | ISO 8601 | End of time range |

**Response:**

```json
{
  "anomalies": [
    {
      "id": "anom_987654",
      "device_id": "dev_123456",
      "timestamp": "2025-01-19T09:15:00Z",
      "type": "vibration_spike",
      "severity": "high",
      "confidence": 0.92,
      "description": "Abnormal vibration pattern detected",
      "metrics": {
        "vibration": 0.25,
        "expected": 0.05,
        "deviation": 400
      }
    }
  ]
}
```

#### Predictive Maintenance

```http
GET /api/v1/analytics/predictions/{device_id}
```

**Response:**

```json
{
  "device_id": "dev_123456",
  "predictions": [
    {
      "component": "motor_bearing",
      "failure_probability": 0.15,
      "time_to_failure_days": 45,
      "confidence": 0.85,
      "recommended_action": "Schedule inspection within 30 days",
      "indicators": [
        "Increasing vibration trend",
        "Temperature anomalies"
      ]
    }
  ],
  "health_score": 78,
  "last_updated": "2025-01-19T10:00:00Z"
}
```

### Alerts

#### Create Alert Rule

```http
POST /api/v1/alerts/rules
Content-Type: application/json

{
  "name": "High Temperature Alert",
  "device_id": "dev_123456",
  "condition": {
    "metric": "motor_temp",
    "operator": ">",
    "threshold": 80,
    "duration": 300
  },
  "severity": "high",
  "notifications": {
    "email": ["operations@example.com"],
    "webhook": "https://example.com/webhook"
  }
}
```

#### Get Alert History

```http
GET /api/v1/alerts/history
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | string | Filter by device |
| `severity` | string | Filter by severity |
| `status` | string | Filter by status (active, acknowledged, resolved) |
| `start_time` | ISO 8601 | Start of time range |
| `end_time` | ISO 8601 | End of time range |

### System

#### Health Check

```http
GET /api/v1/health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.8",
  "timestamp": "2025-01-19T10:30:00Z",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "message_queue": "healthy",
    "analytics": "healthy"
  }
}
```

#### System Metrics

```http
GET /api/v1/metrics
```

**Response (Prometheus format):**

```
# HELP telemetry_ingestion_rate Number of telemetry points ingested per second
# TYPE telemetry_ingestion_rate gauge
telemetry_ingestion_rate 5234.5

# HELP api_request_duration_seconds API request duration in seconds
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{le="0.1"} 8932
api_request_duration_seconds_bucket{le="0.5"} 9823
api_request_duration_seconds_bucket{le="1.0"} 9953
```

## WebSocket API

### Real-time Telemetry

```javascript
const ws = new WebSocket('wss://api.insaiot.com/ws/telemetry/dev_123456');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_jwt_token'
  }));

  // Subscribe to metrics
  ws.send(JSON.stringify({
    type: 'subscribe',
    metrics: ['flow_rate', 'pip', 'vibration']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Telemetry update:', data);
  // {
  //   "device_id": "dev_123456",
  //   "timestamp": "2025-01-19T10:30:00Z",
  //   "flow_rate": 1250.5,
  //   "pip": 2800.0,
  //   "vibration": 0.05
  // }
};
```

### Alert Notifications

```javascript
const ws = new WebSocket('wss://api.insaiot.com/ws/alerts');

ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log('Alert:', alert);
  // {
  //   "id": "alert_123",
  //   "device_id": "dev_123456",
  //   "severity": "high",
  //   "message": "High temperature detected",
  //   "timestamp": "2025-01-19T10:30:00Z"
  // }
};
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "device_id",
        "message": "Device ID is required"
      }
    ],
    "request_id": "req_abc123"
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## SDK Examples

### Python

```python
from insa_iot import Client

# Initialize client
client = Client(
    api_key="your_api_key",
    base_url="https://api.insaiot.com"
)

# Get device
device = client.devices.get("dev_123456")

# Submit telemetry
client.telemetry.submit(
    device_id="dev_123456",
    data={
        "flow_rate": 1250.5,
        "pip": 2800.0
    }
)

# Query telemetry
data = client.telemetry.query(
    device_id="dev_123456",
    start_time="2025-01-19T00:00:00Z",
    end_time="2025-01-19T12:00:00Z"
)
```

### JavaScript/TypeScript

```typescript
import { InsaIoTClient } from '@insa/iot-sdk';

// Initialize client
const client = new InsaIoTClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.insaiot.com'
});

// Get device
const device = await client.devices.get('dev_123456');

// Submit telemetry
await client.telemetry.submit({
  deviceId: 'dev_123456',
  data: {
    flowRate: 1250.5,
    pip: 2800.0
  }
});

// Real-time subscription
client.telemetry.subscribe('dev_123456', (data) => {
  console.log('New telemetry:', data);
});
```

## Support

For API support and questions:

- **Email**: api-support@insaautomation.com
- **Documentation**: https://docs.insaiot.com
- **Status Page**: https://status.insaiot.com
# Real-Time Streaming - Alkhorayef ESP IoT Platform

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [WebSocket API](#websocket-api)
- [Server-Sent Events (SSE) API](#server-sent-events-sse-api)
- [Authentication](#authentication)
- [Client Examples](#client-examples)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

---

## Overview

The Alkhorayef ESP IoT Platform provides comprehensive real-time streaming capabilities for live telemetry updates from ESP wells. We support two real-time protocols:

### WebSocket

- **Full-duplex** bidirectional communication
- **Room-based subscriptions** for multiple wells
- **Heartbeat/ping-pong** for connection health
- **JWT authentication** with role-based access
- **Multi-instance support** via Redis pub/sub
- **Rate limiting** (max 10 messages/second per client)

### Server-Sent Events (SSE)

- **HTTP-based** streaming (simpler than WebSocket)
- **Auto-reconnect** with event replay
- **Keep-alive** mechanism
- **JWT authentication** via query parameter
- **Browser-friendly** (built-in EventSource API)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                       Client Layer                          │
├─────────────────────────────────────────────────────────────┤
│  WebSocket Clients        │        SSE Clients             │
│  (socket.io)              │        (EventSource)           │
└────────────┬──────────────┴────────────────┬───────────────┘
             │                                │
             v                                v
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐          ┌───────────────────┐       │
│  │  WebSocket       │          │   SSE Endpoint    │       │
│  │  Server          │          │   /api/v1/sse     │       │
│  │  (SocketIO)      │          │                   │       │
│  └────────┬─────────┘          └────────┬──────────┘       │
│           │                              │                   │
│           └──────────────┬───────────────┘                   │
│                          │                                   │
│                   ┌──────▼──────────┐                       │
│                   │   Realtime      │                       │
│                   │   Publisher     │                       │
│                   └──────┬──────────┘                       │
└──────────────────────────┼───────────────────────────────────┘
                           │
                   ┌───────▼──────────┐
                   │   Redis Pub/Sub  │
                   │   (Multi-instance)│
                   └──────────────────┘
```

### Message Flow

1. **Telemetry Ingestion**: ESP data arrives at `/api/v1/telemetry/ingest`
2. **Database Storage**: Data is stored in TimescaleDB
3. **Real-Time Publishing**:
   - Publisher emits to WebSocket rooms (via SocketIO)
   - Publisher publishes to Redis channel (for SSE clients)
4. **Client Delivery**: Updates delivered to subscribed clients

---

## WebSocket API

### Connection

#### Endpoint
```
ws://HOST:PORT/socket.io
```

#### Authentication
Pass JWT token in auth object:

```javascript
const socket = io('http://localhost:8000', {
    auth: {
        token: 'YOUR_JWT_TOKEN'
    }
});
```

### Events

#### Client → Server Events

##### `ping`
Heartbeat to maintain connection.

**Request:**
```javascript
socket.emit('ping');
```

**Response:**
```javascript
socket.on('pong', (data) => {
    // data = { timestamp: "2025-11-20T10:30:00Z" }
});
```

##### `subscribe`
Subscribe to a well's updates.

**Request:**
```javascript
socket.emit('subscribe', {
    well_id: 'WELL-001'
});
```

**Response:**
```javascript
socket.on('subscribed', (data) => {
    // data = {
    //     well_id: "WELL-001",
    //     timestamp: "2025-11-20T10:30:00Z"
    // }
});
```

##### `unsubscribe`
Unsubscribe from a well's updates.

**Request:**
```javascript
socket.emit('unsubscribe', {
    well_id: 'WELL-001'
});
```

**Response:**
```javascript
socket.on('unsubscribed', (data) => {
    // data = {
    //     well_id: "WELL-001",
    //     timestamp: "2025-11-20T10:30:00Z"
    // }
});
```

##### `get_stats`
Get connection statistics (admin only for full stats).

**Request:**
```javascript
socket.emit('get_stats');
```

**Response:**
```javascript
socket.on('stats', (data) => {
    // data = {
    //     connected_at: "2025-11-20T10:00:00Z",
    //     message_count: 1234,
    //     subscriptions: ["WELL-001", "WELL-002"]
    // }
});
```

#### Server → Client Events

##### `connected`
Welcome message after successful connection.

```javascript
socket.on('connected', (data) => {
    // data = {
    //     message: "Connected to Alkhorayef ESP IoT Platform",
    //     user_id: "user-123",
    //     username: "john.doe",
    //     timestamp: "2025-11-20T10:30:00Z"
    // }
});
```

##### `telemetry_update`
Real-time telemetry data update.

```javascript
socket.on('telemetry_update', (data) => {
    // data = {
    //     event: "telemetry_update",
    //     timestamp: "2025-11-20T10:30:00Z",
    //     well_id: "WELL-001",
    //     data: {
    //         telemetry_id: 12345,
    //         timestamp: "2025-11-20T10:30:00Z",
    //         flow_rate: 1000.5,
    //         pip: 2000.0,
    //         motor_current: 50.0,
    //         motor_temp: 85.0,
    //         vibration: 3.2,
    //         vsd_frequency: 60.0,
    //         flow_variance: 15.0,
    //         torque: 120.5,
    //         gor: 150.0
    //     }
    // }
});
```

##### `alert`
Critical alerts for a well.

```javascript
socket.on('alert', (data) => {
    // data = {
    //     event: "alert",
    //     timestamp: "2025-11-20T10:30:00Z",
    //     well_id: "WELL-001",
    //     alert: {
    //         type: "high_vibration",
    //         severity: "critical",
    //         message: "Vibration exceeds threshold",
    //         value: 5.2,
    //         threshold: 4.0
    //     }
    // }
});
```

##### `error`
Error messages.

```javascript
socket.on('error', (data) => {
    // data = {
    //     error: "ValidationError",
    //     message: "well_id is required"
    // }
});
```

### Complete WebSocket Example

```javascript
const socket = io('http://localhost:8000', {
    auth: {
        token: 'YOUR_JWT_TOKEN'
    },
    transports: ['websocket', 'polling']
});

// Connection events
socket.on('connect', () => {
    console.log('Connected to server');

    // Subscribe to wells
    socket.emit('subscribe', { well_id: 'WELL-001' });
    socket.emit('subscribe', { well_id: 'WELL-002' });
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

// Data events
socket.on('telemetry_update', (data) => {
    console.log('Telemetry:', data);
    updateDashboard(data);
});

socket.on('alert', (data) => {
    console.log('ALERT:', data);
    showAlertNotification(data);
});

// Error handling
socket.on('error', (data) => {
    console.error('Error:', data);
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
});

// Heartbeat (every 25 seconds)
setInterval(() => {
    if (socket.connected) {
        socket.emit('ping');
    }
}, 25000);
```

---

## Server-Sent Events (SSE) API

### Endpoint

```
GET /api/v1/sse/stream/<well_id>
```

### Authentication

Pass JWT token as query parameter:

```
/api/v1/sse/stream/WELL-001?token=YOUR_JWT_TOKEN
```

### Query Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `token` | Yes | JWT authentication token |
| `last_event_id` | No | Last event ID received (for reconnection) |

### Event Types

#### `connected`
Initial connection confirmation.

```
id: 0
event: connected
data: {"message":"Connected to Alkhorayef ESP IoT Platform SSE stream","well_id":"WELL-001","timestamp":"2025-11-20T10:30:00Z"}
```

#### `heartbeat`
Keep-alive message (sent every 30 seconds).

```
id: 5
event: heartbeat
data: {"timestamp":"2025-11-20T10:31:00Z"}
```

#### `telemetry_update`
Telemetry data update.

```
id: 10
event: telemetry_update
data: {"event":"telemetry_update","timestamp":"2025-11-20T10:30:00Z","well_id":"WELL-001","data":{"flow_rate":1000.5,"pip":2000.0,"motor_current":50.0}}
```

#### `alert`
Critical alert.

```
id: 15
event: alert
data: {"event":"alert","timestamp":"2025-11-20T10:30:00Z","well_id":"WELL-001","alert":{"type":"high_vibration","severity":"critical"}}
```

#### `error`
Error message.

```
event: error
data: {"error":"AuthenticationError","message":"Invalid or expired authentication token"}
```

### Complete SSE Example

```javascript
const wellId = 'WELL-001';
const token = 'YOUR_JWT_TOKEN';
const sseUrl = `http://localhost:8000/api/v1/sse/stream/${wellId}?token=${token}`;

const eventSource = new EventSource(sseUrl);

// Connection events
eventSource.onopen = () => {
    console.log('SSE connection established');
};

eventSource.onerror = (error) => {
    console.error('SSE connection error:', error);

    if (eventSource.readyState === EventSource.CLOSED) {
        console.log('SSE connection closed, will auto-reconnect');
    }
};

// Custom event listeners
eventSource.addEventListener('connected', (event) => {
    const data = JSON.parse(event.data);
    console.log('Connected:', data.message);
});

eventSource.addEventListener('heartbeat', (event) => {
    const data = JSON.parse(event.data);
    console.log('Heartbeat at:', data.timestamp);
});

eventSource.addEventListener('telemetry_update', (event) => {
    const data = JSON.parse(event.data);
    console.log('Telemetry:', data);
    updateDashboard(data);
});

eventSource.addEventListener('alert', (event) => {
    const data = JSON.parse(event.data);
    console.log('ALERT:', data);
    showAlertNotification(data);
});

eventSource.addEventListener('error', (event) => {
    const data = JSON.parse(event.data);
    console.error('Error:', data);
});
```

### SSE Auto-Reconnection

SSE automatically reconnects with the last event ID:

```javascript
// Browser automatically includes Last-Event-ID header on reconnection
// Server uses this to replay missed events
```

---

## Authentication

### Obtaining JWT Token

1. **Login** to get JWT token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }'
```

2. **Response** contains token:

```json
{
    "access_token": "YOUR_JWT_TOKEN_HERE",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

3. **Use token** for WebSocket or SSE connection.

### Token Validation

- Tokens expire after 1 hour (configurable)
- Invalid/expired tokens result in connection rejection
- Refresh tokens before expiration for uninterrupted service

---

## Client Examples

### Browser Examples

- **WebSocket**: `examples/websocket_client.html`
- **SSE**: `examples/sse_client.html`

Open in browser and enter credentials to connect.

### Python Example

```bash
# Install dependencies
pip install python-socketio requests

# Run WebSocket client
python examples/websocket_client.py \
  --server http://localhost:8000 \
  --token YOUR_JWT_TOKEN \
  --well WELL-001 \
  --well WELL-002
```

---

## Performance Tuning

### WebSocket Performance

#### Gunicorn Configuration

```bash
# Single worker with gevent
gunicorn -k gevent -w 1 -b 0.0.0.0:8000 \
  --worker-connections 1000 \
  wsgi:app

# Multiple workers (requires Redis)
gunicorn -k gevent -w 4 -b 0.0.0.0:8000 \
  --worker-connections 1000 \
  wsgi:app
```

#### Connection Limits

- **Max connections per worker**: 1000 (configurable)
- **Recommended**: 1000-5000 connections per server
- **Scaling**: Use multiple servers with load balancer

### SSE Performance

- **Max connections**: Limited by server file descriptors
- **Memory usage**: ~10KB per connection
- **Recommended**: <10,000 connections per server

### Redis Configuration

For multi-instance deployments:

```bash
# Redis configuration
redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

### Rate Limiting

Default: 10 messages/second per client

To adjust:

```python
# In ws_server.py
connection_manager.check_rate_limit(
    sid,
    max_messages=20,  # Increase to 20
    window_seconds=1
)
```

---

## Troubleshooting

### WebSocket Connection Failed

**Symptoms**: Cannot establish WebSocket connection

**Solutions**:
1. Verify server is running with SocketIO support
2. Check JWT token is valid
3. Verify network allows WebSocket connections
4. Try polling transport: `transports: ['polling', 'websocket']`

### SSE Connection Timeout

**Symptoms**: SSE connection drops after 1 minute

**Solutions**:
1. Check proxy/load balancer timeout settings
2. Verify keep-alive messages are being sent (every 30s)
3. Increase proxy timeout: `proxy_read_timeout 300s;` (Nginx)

### No Real-Time Updates

**Symptoms**: Connected but not receiving updates

**Solutions**:
1. Verify subscription to correct well_id
2. Check telemetry is being ingested: `/api/v1/telemetry/ingest`
3. Verify Redis is running (for multi-instance)
4. Check application logs for errors

### High Latency

**Symptoms**: Delayed real-time updates

**Solutions**:
1. Check Redis pub/sub performance
2. Monitor server CPU/memory usage
3. Reduce number of connections per worker
4. Use load balancer for horizontal scaling

### Memory Leaks

**Symptoms**: Increasing memory usage over time

**Solutions**:
1. Ensure proper disconnection handling
2. Limit message queue sizes
3. Monitor connection count
4. Restart workers periodically

---

## Production Deployment

### Prerequisites

1. **Redis** for pub/sub (multi-instance)
2. **Load Balancer** with WebSocket support
3. **SSL/TLS** certificates

### Deployment Checklist

- [ ] Redis configured and running
- [ ] SSL/TLS certificates installed
- [ ] Load balancer configured for WebSocket
- [ ] Gunicorn with gevent worker
- [ ] Connection limits configured
- [ ] Rate limiting enabled
- [ ] Monitoring and alerting set up
- [ ] Log aggregation configured

### Nginx Configuration

```nginx
upstream app_servers {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # WebSocket support
    location /socket.io {
        proxy_pass http://app_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # SSE support
    location /api/v1/sse {
        proxy_pass http://app_servers;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        chunked_transfer_encoding on;
    }

    # Regular API endpoints
    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Monitoring

Monitor these metrics:

- `websocket_connections` - Active WebSocket connections
- `sse_connections` - Active SSE connections
- `websocket_messages_total` - Total messages sent
- `websocket_errors_total` - Total WebSocket errors
- `realtime_publishes_total` - Total real-time publishes
- `realtime_publish_duration_seconds` - Publish latency

### Security Considerations

1. **Authentication**: Always use JWT tokens
2. **Rate Limiting**: Enforce per-client limits
3. **SSL/TLS**: Use HTTPS/WSS in production
4. **Firewall**: Restrict Redis access
5. **Token Expiration**: Rotate tokens regularly

---

## API Reference Summary

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client → Server | Establish connection |
| `disconnect` | Client → Server | Close connection |
| `ping` | Client → Server | Heartbeat |
| `subscribe` | Client → Server | Subscribe to well |
| `unsubscribe` | Client → Server | Unsubscribe from well |
| `get_stats` | Client → Server | Get statistics |
| `connected` | Server → Client | Welcome message |
| `pong` | Server → Client | Heartbeat response |
| `subscribed` | Server → Client | Subscription confirmed |
| `unsubscribed` | Server → Client | Unsubscription confirmed |
| `telemetry_update` | Server → Client | Telemetry data |
| `alert` | Server → Client | Critical alert |
| `stats` | Server → Client | Connection statistics |
| `error` | Server → Client | Error message |

### SSE Events

| Event | Description |
|-------|-------------|
| `connected` | Connection established |
| `heartbeat` | Keep-alive message |
| `telemetry_update` | Telemetry data |
| `alert` | Critical alert |
| `diagnostic_update` | Diagnostic update |
| `error` | Error message |

---

## Support

For issues or questions:

- **Documentation**: `/docs`
- **GitHub Issues**: https://github.com/your-org/esp-platform/issues
- **Email**: support@your-domain.com

---

**Version**: 1.0.0
**Last Updated**: 2025-11-20
**Week 3 Feature Implementation**

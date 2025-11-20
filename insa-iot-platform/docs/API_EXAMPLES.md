# Alkhorayef ESP IoT Platform - API Examples

This document provides comprehensive code examples for integrating with the Alkhorayef ESP IoT Platform API.

## Table of Contents

- [Authentication](#authentication)
- [Health Checks](#health-checks)
- [Telemetry Operations](#telemetry-operations)
- [Diagnostic Operations](#diagnostic-operations)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Authentication

> **Note**: JWT authentication is planned for future releases. Currently, the API is accessible without authentication for development purposes.

### Future: Obtaining JWT Token (Planned)

```python
import requests

# Login to get JWT token
response = requests.post(
    'https://api.insaautomation.com/api/v1/auth/login',
    json={
        'username': 'your_username',
        'password': 'your_password'
    }
)

token = response.json()['access_token']

# Use token in subsequent requests
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
```

---

## Health Checks

### Check API Health (Python)

```python
import requests

# General health check
response = requests.get('http://localhost:8000/health')
health = response.json()

print(f"Status: {health['status']}")
print(f"Database: {health['dependencies']['database']['status']}")
```

### Liveness Probe (cURL)

```bash
# Kubernetes liveness probe
curl -X GET http://localhost:8000/health/live

# Expected response:
# {
#   "status": "alive",
#   "timestamp": "2025-11-20T14:30:00Z",
#   "service": "alkhorayef-esp-iot-platform"
# }
```

### Readiness Probe (JavaScript/Fetch)

```javascript
// Check if API is ready to serve traffic
fetch('http://localhost:8000/health/ready')
  .then(response => response.json())
  .then(data => {
    console.log('Ready:', data.status === 'ready');
    console.log('Database:', data.dependencies.database.status);
  })
  .catch(error => console.error('Health check failed:', error));
```

---

## Telemetry Operations

### Ingest Single Telemetry Reading

#### Python (requests)

```python
import requests
from datetime import datetime

telemetry_data = {
    "well_id": "WELL-001",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "flow_rate": 2500.5,
    "pip": 250.0,
    "motor_current": 45.2,
    "motor_temp": 85.5,
    "vibration": 3.2,
    "vsd_frequency": 60.0,
    "flow_variance": 15.0,
    "torque": 120.5,
    "gor": 150.0
}

response = requests.post(
    'http://localhost:8000/api/v1/telemetry/ingest',
    json=telemetry_data
)

if response.status_code == 201:
    result = response.json()
    print(f"✓ Telemetry ingested: ID {result['telemetry_id']}")
else:
    print(f"✗ Error: {response.json()['message']}")
```

#### cURL

```bash
curl -X POST http://localhost:8000/api/v1/telemetry/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "well_id": "WELL-001",
    "timestamp": "2025-11-20T14:30:00Z",
    "flow_rate": 2500.5,
    "pip": 250.0,
    "motor_current": 45.2,
    "motor_temp": 85.5,
    "vibration": 3.2,
    "vsd_frequency": 60.0,
    "flow_variance": 15.0,
    "torque": 120.5,
    "gor": 150.0
  }'
```

#### JavaScript/Fetch

```javascript
const telemetryData = {
  well_id: "WELL-001",
  timestamp: new Date().toISOString(),
  flow_rate: 2500.5,
  pip: 250.0,
  motor_current: 45.2,
  motor_temp: 85.5,
  vibration: 3.2,
  vsd_frequency: 60.0,
  flow_variance: 15.0,
  torque: 120.5,
  gor: 150.0
};

fetch('http://localhost:8000/api/v1/telemetry/ingest', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(telemetryData)
})
  .then(response => response.json())
  .then(data => {
    console.log('Telemetry ingested:', data.telemetry_id);
  })
  .catch(error => console.error('Error:', error));
```

### Batch Ingest Telemetry

#### Python (requests)

```python
import requests
from datetime import datetime, timedelta

# Generate batch of readings
base_time = datetime.utcnow()
readings = []

for i in range(10):
    reading = {
        "well_id": "WELL-001",
        "timestamp": (base_time + timedelta(minutes=i)).isoformat() + "Z",
        "flow_rate": 2500.5 + i * 10,
        "pip": 250.0 + i * 2,
        "motor_current": 45.2 + i * 0.1,
        "motor_temp": 85.5 + i * 0.2,
        "vibration": 3.2 + i * 0.05,
        "vsd_frequency": 60.0,
        "flow_variance": 15.0 - i * 0.5,
        "torque": 120.5 + i * 1,
        "gor": 150.0 + i * 2
    }
    readings.append(reading)

# Send batch
response = requests.post(
    'http://localhost:8000/api/v1/telemetry/batch',
    json={"readings": readings}
)

if response.status_code == 201:
    result = response.json()
    print(f"✓ Batch ingested: {result['batch_size']} readings in {result['duration_ms']:.2f}ms")
else:
    print(f"✗ Error: {response.json()['message']}")
```

#### cURL

```bash
curl -X POST http://localhost:8000/api/v1/telemetry/batch \
  -H "Content-Type: application/json" \
  -d '{
    "readings": [
      {
        "well_id": "WELL-001",
        "timestamp": "2025-11-20T14:30:00Z",
        "flow_rate": 2500.5,
        "pip": 250.0,
        "motor_current": 45.2,
        "motor_temp": 85.5,
        "vibration": 3.2,
        "vsd_frequency": 60.0,
        "flow_variance": 15.0,
        "torque": 120.5,
        "gor": 150.0
      },
      {
        "well_id": "WELL-001",
        "timestamp": "2025-11-20T14:31:00Z",
        "flow_rate": 2510.2,
        "pip": 251.5,
        "motor_current": 45.5,
        "motor_temp": 86.0,
        "vibration": 3.3,
        "vsd_frequency": 60.0,
        "flow_variance": 14.5,
        "torque": 121.0,
        "gor": 151.0
      }
    ]
  }'
```

### Get Latest Telemetry

#### Python

```python
import requests

well_id = "WELL-001"
response = requests.get(f'http://localhost:8000/api/v1/telemetry/wells/{well_id}/latest')

if response.status_code == 200:
    data = response.json()
    telemetry = data['telemetry']
    print(f"Latest reading for {well_id}:")
    print(f"  Flow Rate: {telemetry['flow_rate']} BPD")
    print(f"  PIP: {telemetry['pip']} PSI")
    print(f"  Motor Temp: {telemetry['motor_temp']}°C")
elif response.status_code == 404:
    print(f"No telemetry found for well {well_id}")
```

#### cURL

```bash
curl -X GET http://localhost:8000/api/v1/telemetry/wells/WELL-001/latest
```

### Get Telemetry History

#### Python

```python
import requests
import pandas as pd

well_id = "WELL-001"
hours = 24

response = requests.get(
    f'http://localhost:8000/api/v1/telemetry/wells/{well_id}/history',
    params={'hours': hours}
)

if response.status_code == 200:
    data = response.json()

    # Convert to pandas DataFrame for analysis
    df = pd.DataFrame(data['telemetry'])

    print(f"Retrieved {len(df)} readings for last {hours} hours")
    print(f"Average flow rate: {df['flow_rate'].mean():.2f} BPD")
    print(f"Max motor temp: {df['motor_temp'].max():.2f}°C")

    # Plot if matplotlib is available
    try:
        import matplotlib.pyplot as plt

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        df['flow_rate'].plot(ax=axes[0, 0], title='Flow Rate')
        df['pip'].plot(ax=axes[0, 1], title='Pump Intake Pressure')
        df['motor_temp'].plot(ax=axes[1, 0], title='Motor Temperature')
        df['vibration'].plot(ax=axes[1, 1], title='Vibration')

        plt.tight_layout()
        plt.savefig(f'{well_id}_telemetry.png')
        print(f"Chart saved as {well_id}_telemetry.png")
    except ImportError:
        pass
```

#### JavaScript

```javascript
async function getTelemetryHistory(wellId, hours = 24) {
  const response = await fetch(
    `http://localhost:8000/api/v1/telemetry/wells/${wellId}/history?hours=${hours}`
  );

  const data = await response.json();

  if (data.success) {
    console.log(`Retrieved ${data.count} readings`);

    // Process telemetry data
    const flowRates = data.telemetry.map(t => t.flow_rate);
    const avgFlowRate = flowRates.reduce((a, b) => a + b) / flowRates.length;

    console.log(`Average flow rate: ${avgFlowRate.toFixed(2)} BPD`);

    return data.telemetry;
  } else {
    throw new Error('Failed to fetch telemetry history');
  }
}

// Usage
getTelemetryHistory('WELL-001', 24)
  .then(telemetry => {
    // Use telemetry data for visualization
  })
  .catch(error => console.error(error));
```

### Get Well Summary

#### Python

```python
import requests

well_id = "WELL-001"
response = requests.get(f'http://localhost:8000/api/v1/telemetry/wells/{well_id}/summary')

if response.status_code == 200:
    summary = response.json()['summary']

    print(f"\nWell {summary['well_id']} - Summary (last {summary['period_hours']} hours)")
    print(f"Total readings: {summary['reading_count']}")
    print("\nFlow Rate:")
    print(f"  Min: {summary['flow_rate']['min']:.2f} BPD")
    print(f"  Max: {summary['flow_rate']['max']:.2f} BPD")
    print(f"  Avg: {summary['flow_rate']['avg']:.2f} BPD")
    print(f"  StdDev: {summary['flow_rate']['stddev']:.2f}")
    print("\nMotor Temperature:")
    print(f"  Min: {summary['motor_temp']['min']:.2f}°C")
    print(f"  Max: {summary['motor_temp']['max']:.2f}°C")
    print(f"  Avg: {summary['motor_temp']['avg']:.2f}°C")
```

---

## Diagnostic Operations

### Analyze Telemetry Data

#### Python

```python
import requests

diagnostic_request = {
    "well_id": "WELL-001",
    "telemetry": {
        "timestamp": "2025-11-20T14:30:00Z",
        "flow_rate": 2500.5,
        "pip": 250.0,
        "motor_current": 45.2,
        "motor_temp": 95.5,  # High temperature
        "vibration": 3.2,
        "vsd_frequency": 60.0,
        "flow_variance": 15.0,
        "torque": 120.5,
        "gor": 150.0
    },
    "store_result": True
}

response = requests.post(
    'http://localhost:8000/api/v1/diagnostics/analyze',
    json=diagnostic_request
)

if response.status_code == 200:
    result = response.json()
    diagnostic = result['diagnostic']

    print(f"\n{'='*60}")
    print(f"DIAGNOSTIC REPORT - {result['well_id']}")
    print(f"{'='*60}")
    print(f"Diagnosis: {diagnostic['diagnosis']}")
    print(f"Confidence: {diagnostic['confidence']*100:.1f}%")
    print(f"Severity: {diagnostic['severity'].upper()}")
    print(f"\nDescription:")
    print(f"  {diagnostic['description']}")
    print(f"\nRoot Cause:")
    print(f"  {diagnostic['root_cause']}")
    print(f"\nRecommended Actions:")
    for i, action in enumerate(diagnostic['recommended_actions'], 1):
        print(f"  {i}. {action}")
    print(f"\nExpected Resolution Time: {diagnostic['expected_resolution_time']}")
    print(f"{'='*60}\n")
```

#### cURL

```bash
curl -X POST http://localhost:8000/api/v1/diagnostics/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "well_id": "WELL-001",
    "telemetry": {
      "flow_rate": 2500.5,
      "pip": 250.0,
      "motor_current": 45.2,
      "motor_temp": 95.5,
      "vibration": 3.2,
      "vsd_frequency": 60.0,
      "flow_variance": 15.0,
      "torque": 120.5,
      "gor": 150.0
    },
    "store_result": true
  }'
```

### Analyze Latest Telemetry

#### Python

```python
import requests

well_id = "WELL-001"
response = requests.post(
    f'http://localhost:8000/api/v1/diagnostics/wells/{well_id}/analyze-latest',
    params={'store_result': 'true'}
)

if response.status_code == 200:
    result = response.json()
    diagnostic = result['diagnostic']

    # Check severity and alert if critical
    if diagnostic['severity'] in ['high', 'critical']:
        print(f"⚠️  ALERT: {diagnostic['diagnosis']} detected in {well_id}")
        print(f"Severity: {diagnostic['severity'].upper()}")
        print(f"Immediate action required!")

        # Send alert (email, SMS, etc.)
        # send_alert(well_id, diagnostic)
    else:
        print(f"✓ Well {well_id}: {diagnostic['diagnosis']}")
```

### Get Diagnostic History

#### Python

```python
import requests

well_id = "WELL-001"
limit = 10

response = requests.get(
    f'http://localhost:8000/api/v1/diagnostics/wells/{well_id}/history',
    params={'limit': limit}
)

if response.status_code == 200:
    data = response.json()

    print(f"\nDiagnostic History for {well_id} (last {data['count']} results)")
    print(f"{'='*80}")

    for i, diagnostic in enumerate(data['diagnostics'], 1):
        print(f"\n{i}. {diagnostic['timestamp']}")
        print(f"   Diagnosis: {diagnostic['diagnosis']}")
        print(f"   Severity: {diagnostic['severity']}")
        print(f"   Confidence: {diagnostic['confidence']*100:.1f}%")
```

### Get Critical Diagnostics

#### Python

```python
import requests

response = requests.get(
    'http://localhost:8000/api/v1/diagnostics/critical',
    params={'limit': 50}
)

if response.status_code == 200:
    data = response.json()

    print(f"\nCritical Diagnostics Across All Wells")
    print(f"{'='*80}")
    print(f"Found {data['count']} critical issues\n")

    # Group by well
    from collections import defaultdict
    by_well = defaultdict(list)

    for diagnostic in data['diagnostics']:
        well_id = diagnostic['telemetry_snapshot']['well_id']
        by_well[well_id].append(diagnostic)

    # Display summary
    for well_id, diagnostics in sorted(by_well.items()):
        print(f"\n{well_id}: {len(diagnostics)} critical issue(s)")
        for diagnostic in diagnostics:
            print(f"  - {diagnostic['diagnosis']} ({diagnostic['severity']})")
```

---

## Error Handling

### Python Error Handling Best Practices

```python
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

def ingest_telemetry_safe(telemetry_data, max_retries=3):
    """
    Safely ingest telemetry with retry logic and error handling.
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(
                'http://localhost:8000/api/v1/telemetry/ingest',
                json=telemetry_data,
                timeout=10  # 10 second timeout
            )

            # Check status code
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                # Validation error - don't retry
                error = response.json()
                print(f"Validation error: {error['message']}")
                if 'field' in error:
                    print(f"Field: {error['field']}")
                return None
            elif response.status_code == 500:
                # Server error - retry
                print(f"Server error on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    continue
                else:
                    print("Max retries reached")
                    return None
            else:
                print(f"Unexpected status code: {response.status_code}")
                return None

        except Timeout:
            print(f"Request timeout on attempt {attempt + 1}/{max_retries}")
            if attempt == max_retries - 1:
                print("Max retries reached")
                return None

        except ConnectionError:
            print(f"Connection error on attempt {attempt + 1}/{max_retries}")
            if attempt == max_retries - 1:
                print("Max retries reached")
                return None

        except RequestException as e:
            print(f"Request exception: {e}")
            return None

    return None

# Usage
result = ingest_telemetry_safe(telemetry_data)
if result:
    print(f"✓ Success: {result['telemetry_id']}")
else:
    print("✗ Failed to ingest telemetry")
```

### JavaScript Error Handling

```javascript
async function ingestTelemetrySafe(telemetryData, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch('http://localhost:8000/api/v1/telemetry/ingest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(telemetryData),
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });

      if (response.ok) {
        return await response.json();
      } else if (response.status === 400) {
        // Validation error - don't retry
        const error = await response.json();
        console.error('Validation error:', error.message);
        return null;
      } else if (response.status === 500) {
        // Server error - retry
        console.warn(`Server error on attempt ${attempt + 1}/${maxRetries}`);
        if (attempt < maxRetries - 1) continue;
        throw new Error('Max retries reached');
      }
    } catch (error) {
      console.error(`Request failed on attempt ${attempt + 1}:`, error);
      if (attempt === maxRetries - 1) throw error;
    }
  }
}

// Usage
try {
  const result = await ingestTelemetrySafe(telemetryData);
  if (result) {
    console.log('✓ Success:', result.telemetry_id);
  }
} catch (error) {
  console.error('✗ Failed to ingest telemetry:', error);
}
```

---

## Best Practices

### 1. Batch Processing for High-Throughput

```python
import requests
from collections import deque
import time

class TelemetryBatcher:
    """
    Buffer telemetry readings and send in batches for optimal performance.
    """
    def __init__(self, batch_size=100, max_wait_seconds=5):
        self.batch_size = batch_size
        self.max_wait_seconds = max_wait_seconds
        self.buffer = deque()
        self.last_flush = time.time()

    def add(self, reading):
        """Add a reading to the buffer."""
        self.buffer.append(reading)

        # Auto-flush if batch is full or max wait time exceeded
        if len(self.buffer) >= self.batch_size or \
           time.time() - self.last_flush >= self.max_wait_seconds:
            self.flush()

    def flush(self):
        """Send buffered readings to API."""
        if not self.buffer:
            return

        readings = []
        while self.buffer and len(readings) < self.batch_size:
            readings.append(self.buffer.popleft())

        response = requests.post(
            'http://localhost:8000/api/v1/telemetry/batch',
            json={'readings': readings}
        )

        if response.status_code == 201:
            result = response.json()
            print(f"✓ Flushed {result['batch_size']} readings")
        else:
            print(f"✗ Batch failed: {response.json()['message']}")
            # Re-add to buffer for retry
            self.buffer.extendleft(reversed(readings))

        self.last_flush = time.time()

# Usage
batcher = TelemetryBatcher(batch_size=100, max_wait_seconds=5)

# Add readings as they come in
for reading in sensor_data_stream:
    batcher.add(reading)

# Flush any remaining at the end
batcher.flush()
```

### 2. Connection Pooling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create session with connection pooling and retry logic
session = requests.Session()

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
)

adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=retry_strategy
)

session.mount("http://", adapter)
session.mount("https://", adapter)

# Use session for all requests
response = session.post(
    'http://localhost:8000/api/v1/telemetry/ingest',
    json=telemetry_data
)
```

### 3. Async Operations (Python asyncio)

```python
import asyncio
import aiohttp

async def ingest_telemetry_async(session, telemetry_data):
    """Async telemetry ingestion."""
    async with session.post(
        'http://localhost:8000/api/v1/telemetry/ingest',
        json=telemetry_data
    ) as response:
        return await response.json()

async def ingest_multiple_async(telemetry_list):
    """Ingest multiple readings concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [
            ingest_telemetry_async(session, data)
            for data in telemetry_list
        ]
        results = await asyncio.gather(*tasks)
        return results

# Usage
telemetry_list = [reading1, reading2, reading3, ...]
results = asyncio.run(ingest_multiple_async(telemetry_list))
print(f"Ingested {len(results)} readings")
```

### 4. Monitoring and Alerting

```python
import requests
import time
from datetime import datetime

class ESPMonitor:
    """Monitor ESP wells and alert on critical issues."""

    def __init__(self, well_ids, check_interval_seconds=60):
        self.well_ids = well_ids
        self.check_interval = check_interval_seconds

    def check_well(self, well_id):
        """Check well status and run diagnostics."""
        # Analyze latest telemetry
        response = requests.post(
            f'http://localhost:8000/api/v1/diagnostics/wells/{well_id}/analyze-latest'
        )

        if response.status_code == 200:
            result = response.json()
            diagnostic = result['diagnostic']

            # Alert on critical issues
            if diagnostic['severity'] in ['high', 'critical']:
                self.send_alert(well_id, diagnostic)

            return diagnostic
        else:
            print(f"Failed to check {well_id}")
            return None

    def send_alert(self, well_id, diagnostic):
        """Send alert for critical issues."""
        message = f"""
        CRITICAL ALERT: {well_id}

        Diagnosis: {diagnostic['diagnosis']}
        Severity: {diagnostic['severity'].upper()}
        Confidence: {diagnostic['confidence']*100:.1f}%

        Root Cause: {diagnostic['root_cause']}

        Immediate Actions:
        {chr(10).join(f"- {action}" for action in diagnostic['recommended_actions'])}

        Expected Resolution Time: {diagnostic['expected_resolution_time']}

        Timestamp: {datetime.now().isoformat()}
        """

        print(message)

        # Send via email, SMS, Slack, etc.
        # send_email(subject=f"CRITICAL: {well_id}", body=message)
        # send_sms(message)
        # send_slack(message)

    def monitor_loop(self):
        """Continuous monitoring loop."""
        print(f"Starting ESP monitor for {len(self.well_ids)} wells")
        print(f"Check interval: {self.check_interval} seconds")

        while True:
            for well_id in self.well_ids:
                try:
                    diagnostic = self.check_well(well_id)
                    if diagnostic:
                        status = "✓" if diagnostic['diagnosis'] == 'NORMAL_OPERATION' else "⚠"
                        print(f"{status} {well_id}: {diagnostic['diagnosis']}")
                except Exception as e:
                    print(f"✗ Error checking {well_id}: {e}")

            time.sleep(self.check_interval)

# Usage
monitor = ESPMonitor(
    well_ids=['WELL-001', 'WELL-002', 'WELL-003'],
    check_interval_seconds=60
)

# Start monitoring
monitor.monitor_loop()
```

---

## Additional Resources

- **OpenAPI Specification**: `/api/v1/openapi.yaml`
- **Swagger UI**: `/api/v1/docs`
- **ReDoc**: `/api/v1/redoc`
- **Health Endpoint**: `/health`
- **Support**: contact@insaautomation.com

---

© 2025 INSA Automation. All rights reserved.

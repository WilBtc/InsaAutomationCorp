# Alkhorayef ESP IoT Platform - Quick Start Guide

## Installation

1. **Clone and navigate to the project**
   ```bash
   cd /home/wil/insa-iot-platform
   ```

2. **Set up environment variables**
   ```bash
   cp app/.env.example .env
   nano .env  # Edit with your database and Redis credentials
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Option 1: Quick Start Script (Recommended)
```bash
python run_modular_app.py
```

### Option 2: Direct Flask
```bash
python -m app
```

### Option 3: Production with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Testing the API

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ready",
  "timestamp": "2025-11-20T14:30:00.000Z",
  "service": "alkhorayef-esp-iot-platform",
  "version": "1.0.0",
  "environment": "development",
  "dependencies": {
    "database": {
      "status": "healthy",
      "type": "postgresql"
    }
  }
}
```

### 2. Ingest Telemetry Data
```bash
curl -X POST http://localhost:8000/api/v1/telemetry/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "well_id": "WELL-001",
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

### 3. Get Latest Telemetry
```bash
curl http://localhost:8000/api/v1/telemetry/wells/WELL-001/latest
```

### 4. Analyze Latest Telemetry
```bash
curl -X POST http://localhost:8000/api/v1/diagnostics/wells/WELL-001/analyze-latest
```

### 5. Get Diagnostic History
```bash
curl http://localhost:8000/api/v1/diagnostics/wells/WELL-001/history?limit=5
```

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe |
| POST | `/api/v1/telemetry/ingest` | Ingest single telemetry |
| POST | `/api/v1/telemetry/batch` | Ingest batch telemetry |
| GET | `/api/v1/telemetry/wells/<id>/latest` | Get latest reading |
| GET | `/api/v1/telemetry/wells/<id>/history` | Get telemetry history |
| GET | `/api/v1/telemetry/wells/<id>/summary` | Get well summary |
| POST | `/api/v1/diagnostics/analyze` | Analyze telemetry |
| POST | `/api/v1/diagnostics/wells/<id>/analyze-latest` | Analyze latest |
| GET | `/api/v1/diagnostics/wells/<id>/history` | Get diagnostics |
| GET | `/api/v1/diagnostics/critical` | Get critical issues |

## Project Structure

```
app/
├── __init__.py              # Application factory
├── core/                    # Core functionality
│   ├── config.py            # Configuration management
│   ├── logging.py           # Structured logging
│   └── exceptions.py        # Custom exceptions
├── db/                      # Database layer
│   ├── connection.py        # Connection pooling
│   └── models.py            # Data models
├── services/                # Business logic
│   ├── telemetry_service.py
│   └── diagnostic_service.py
└── api/                     # REST API
    ├── routes/              # Endpoints
    │   ├── health.py
    │   ├── telemetry.py
    │   └── diagnostics.py
    └── middleware/          # Middleware
        └── error_handler.py
```

## Configuration

All configuration is done via environment variables in `.env`:

### Required Variables
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=esp_telemetry
POSTGRES_USER=alkhorayef
POSTGRES_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Security
SECRET_KEY=your_secret_key_at_least_32_characters_long
```

### Optional Variables
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
LOG_FORMAT=json
TELEMETRY_RETENTION_DAYS=30
```

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify database exists: `createdb esp_telemetry`

### Import Errors
- Install all dependencies: `pip install -r requirements.txt`
- Ensure Python 3.12+ is being used

### Port Already in Use
- Change PORT in `.env` file
- Or stop the service using port 8000

## Next Steps

1. Read the full documentation: `app/README.md`
2. Check the implementation summary: `MODULAR_STRUCTURE_SUMMARY.md`
3. Review the expert architecture plan: `EXPERT_ARCHITECTURE_PLAN.md`
4. Set up monitoring and alerting
5. Implement authentication and authorization
6. Add comprehensive test suite

## Support

For detailed documentation, see:
- `app/README.md` - Complete application documentation
- `MODULAR_STRUCTURE_SUMMARY.md` - Implementation summary
- `EXPERT_ARCHITECTURE_PLAN.md` - Architecture design

# Alkhorayef ESP IoT Platform - Application Module

This directory contains the modular Python application structure for the Alkhorayef ESP IoT Platform.

## Directory Structure

```
app/
├── __init__.py              # Flask application factory
├── api/                     # REST API layer
│   ├── __init__.py
│   ├── routes/              # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints (/health/*)
│   │   ├── telemetry.py     # Telemetry endpoints (/api/v1/telemetry/*)
│   │   └── diagnostics.py   # Diagnostic endpoints (/api/v1/diagnostics/*)
│   └── middleware/          # Request/response middleware
│       ├── __init__.py
│       └── error_handler.py # Global error handling
├── core/                    # Core functionality
│   ├── __init__.py
│   ├── config.py            # Configuration management with validation
│   ├── logging.py           # Structured JSON logging
│   └── exceptions.py        # Custom exception classes
├── db/                      # Database layer
│   ├── __init__.py
│   ├── connection.py        # PostgreSQL connection pooling
│   └── models.py            # Data models and SQL queries
└── services/                # Business logic layer
    ├── __init__.py
    ├── telemetry_service.py # Telemetry business logic
    └── diagnostic_service.py # Diagnostic business logic
```

## Key Features

### 1. Configuration Management (`core/config.py`)
- Environment variable-based configuration
- Validation on startup
- Type-safe configuration classes
- Separate configs for database, Redis, logging, security, and telemetry

### 2. Structured Logging (`core/logging.py`)
- JSON-formatted logs for production
- Text-formatted logs for development
- Automatic log rotation
- Contextual logging with extra fields
- Performance and audit logging helpers

### 3. Exception Handling (`core/exceptions.py`)
- Custom exception hierarchy
- Detailed error context
- Consistent error responses
- Proper HTTP status code mapping

### 4. Database Connection Pooling (`db/connection.py`)
- Thread-safe PostgreSQL connection pool
- Automatic retry logic
- Context managers for safe resource handling
- Query execution with parameter binding

### 5. Data Models (`db/models.py`)
- Type-safe dataclasses for telemetry and diagnostics
- Built-in validation
- SQL table definitions
- Common query templates

### 6. Service Layer (`services/`)
- Business logic separation from API routes
- Reusable service methods
- Proper error handling and logging
- Performance monitoring

### 7. API Routes (`api/routes/`)
- RESTful endpoint design
- Request validation
- Consistent response format
- Comprehensive error handling

### 8. Middleware (`api/middleware/`)
- Global error handler registration
- CORS header management
- Security headers
- Request/response logging

## Running the Application

### Development Mode

```bash
# Set environment variables
cp app/.env.example .env
# Edit .env with your actual values

# Run with Flask development server
python -m app

# Or use the main app.py
python app.py
```

### Production Mode

```bash
# Using gunicorn (recommended)
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Using gunicorn with specific configuration
gunicorn -w 4 -b 0.0.0.0:8000 \
  --worker-class sync \
  --timeout 30 \
  --access-logfile - \
  --error-logfile - \
  app:app
```

## API Endpoints

### Health Checks
- `GET /health` - General health check
- `GET /health/live` - Liveness probe (always returns 200 if app is running)
- `GET /health/ready` - Readiness probe (checks dependencies)
- `GET /health/startup` - Startup probe (checks initialization)

### Telemetry API
- `POST /api/v1/telemetry/ingest` - Ingest single telemetry reading
- `POST /api/v1/telemetry/batch` - Ingest batch of readings
- `GET /api/v1/telemetry/wells/<well_id>/latest` - Get latest reading
- `GET /api/v1/telemetry/wells/<well_id>/history?hours=24` - Get history
- `GET /api/v1/telemetry/wells/<well_id>/summary` - Get well summary

### Diagnostics API
- `POST /api/v1/diagnostics/analyze` - Analyze telemetry data
- `POST /api/v1/diagnostics/wells/<well_id>/analyze-latest` - Analyze latest reading
- `GET /api/v1/diagnostics/wells/<well_id>/history?limit=10` - Get diagnostic history
- `GET /api/v1/diagnostics/critical?limit=50` - Get critical diagnostics

## Example Usage

### Ingest Telemetry
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

### Analyze Latest Telemetry
```bash
curl -X POST http://localhost:8000/api/v1/diagnostics/wells/WELL-001/analyze-latest
```

### Get Telemetry History
```bash
curl http://localhost:8000/api/v1/telemetry/wells/WELL-001/history?hours=24
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for all available options.

### Key Configuration Sections

1. **Application**: Environment, debug mode, host, port
2. **Database**: PostgreSQL connection and pool settings
3. **Redis**: Cache configuration
4. **Logging**: Log level, format, rotation
5. **Security**: JWT, CORS, rate limiting
6. **Telemetry**: Data retention, batch size, timeouts

## Error Handling

All errors return consistent JSON responses:

```json
{
  "error": "ValidationError",
  "message": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "flow_rate",
    "errors": ["flow_rate must be non-negative"]
  }
}
```

## Logging

Logs are written in JSON format for easy parsing and analysis:

```json
{
  "timestamp": "2025-11-20T14:30:00.000Z",
  "level": "INFO",
  "logger": "app.services.telemetry_service",
  "message": "Telemetry ingested successfully",
  "environment": "production",
  "module": "telemetry_service",
  "function": "ingest_telemetry",
  "line": 45,
  "well_id": "WELL-001",
  "telemetry_id": 12345
}
```

## Testing

```bash
# Run tests (when test suite is added)
pytest app/tests/

# Run with coverage
pytest --cov=app app/tests/
```

## Type Checking

```bash
# Run mypy type checker
mypy app/
```

## Code Formatting

```bash
# Format code with black
black app/

# Check code style with flake8
flake8 app/
```

## Database Initialization

The application automatically creates required database tables on startup. To manually initialize:

```python
from app.db import get_db_pool, SQL_CREATE_TABLES

db_pool = get_db_pool()
db_pool.execute_query(SQL_CREATE_TABLES, fetch=False)
```

## Development Guidelines

1. **Use type hints** throughout the codebase
2. **Add docstrings** to all functions and classes
3. **Follow PEP 8** style guide
4. **Log important operations** with appropriate levels
5. **Use custom exceptions** for better error handling
6. **Validate input data** at API boundaries
7. **Use context managers** for resource management
8. **Write tests** for all new functionality

## Architecture Principles

- **Separation of Concerns**: API, business logic, and data access are separate
- **Dependency Injection**: Services receive dependencies explicitly
- **Configuration as Code**: Type-safe configuration with validation
- **Fail Fast**: Validate configuration and connections on startup
- **Error Transparency**: Clear error messages with context
- **Performance Monitoring**: Built-in performance logging
- **Production Ready**: Structured logging, health checks, graceful shutdown

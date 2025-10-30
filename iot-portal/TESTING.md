# Testing Guide - INSA Advanced IIoT Platform v2.0

**Version**: 2.0
**Updated**: October 28, 2025
**Test Suite**: 118 tests (58 unit, 60 integration)
**Current Coverage**: 13% (Target: 80%+)

## Quick Start

```bash
# Install development dependencies
./venv/bin/pip install -r requirements-dev.txt

# Run all tests
./venv/bin/pytest

# Run with coverage report
./venv/bin/pytest --cov=. --cov-report=html

# Run specific test categories
./venv/bin/pytest -m unit          # Unit tests only
./venv/bin/pytest -m integration   # Integration tests only
./venv/bin/pytest -m analytics     # Analytics tests only
./venv/bin/pytest -m rbac          # RBAC tests only

# Run fast tests only (skip slow tests)
./venv/bin/pytest -m "not slow"

# Run specific test file
./venv/bin/pytest tests/unit/test_analytics.py

# View HTML coverage report
firefox htmlcov/index.html
```

## Test Organization

```
tests/
├── __init__.py
├── unit/                   # Unit tests (58 tests)
│   ├── __init__.py
│   ├── test_analytics.py  # 23 tests for Feature 1
│   └── test_rbac.py       # 35 tests for Feature 5
├── integration/            # Integration tests (60 tests)
│   ├── __init__.py
│   ├── test_webhook.py    # 12 tests for webhook system
│   ├── test_redis_cache.py # 18 tests for cache layer
│   ├── test_mqtt.py       # 15 tests for MQTT broker
│   └── test_rule_engine.py # 15 tests for rule engine
└── e2e/                    # End-to-end tests (future)
    └── __init__.py
```

## Test Categories

### Unit Tests (58 tests)

**Analytics Module (23 tests)**
- Time-series analysis (6 tests)
- Trend detection (4 tests)
- Statistical summary (3 tests)
- Correlation analysis (3 tests)
- Forecasting (4 tests)
- Edge cases (3 tests)

**RBAC Module (35 tests)**
- User registration (5 tests)
- User login (5 tests)
- Token refresh (3 tests)
- User management (9 tests)
- Role management (6 tests)
- Audit logs (3 tests)
- Permission checks (4 tests)

### Integration Tests (60 tests)

**Webhook System (12 tests)**
- Delivery and retry logic
- HMAC signature validation
- SSRF protection
- Rate limiting
- Timeout handling
- Concurrent delivery

**Redis Cache (18 tests)**
- Basic operations (set/get/delete)
- TTL expiration
- Pattern matching
- Hash/list/sorted set operations
- Performance optimization
- Integration with app

**MQTT Broker (15 tests)**
- Connection management
- Publish/subscribe
- QoS levels (0, 1, 2)
- Topic wildcards
- Message callbacks
- Performance/throughput

**Rule Engine (15 tests)**
- Condition evaluation (6 types)
- Action execution (email, webhook, log)
- Rule CRUD operations
- Performance testing
- Cooldown periods
- Notification delivery

## Test Markers

```python
# Category markers
@pytest.mark.unit         # Fast, isolated unit tests
@pytest.mark.integration  # Tests with external dependencies
@pytest.mark.e2e          # Full system end-to-end tests

# Feature markers
@pytest.mark.analytics    # Analytics module tests
@pytest.mark.rbac         # RBAC module tests
@pytest.mark.webhook      # Webhook system tests
@pytest.mark.cache        # Redis cache tests
@pytest.mark.mqtt         # MQTT broker tests
@pytest.mark.rules        # Rule engine tests

# Performance markers
@pytest.mark.fast         # Tests that run in <100ms
@pytest.mark.slow         # Tests that take >1 second
```

## Running Tests by Marker

```bash
# Run only analytics tests
./venv/bin/pytest -m analytics

# Run only unit tests
./venv/bin/pytest -m unit

# Run unit tests for analytics
./venv/bin/pytest -m "unit and analytics"

# Skip slow tests
./venv/bin/pytest -m "not slow"

# Run specific test class
./venv/bin/pytest tests/unit/test_analytics.py::TestTimeseriesAnalytics

# Run specific test method
./venv/bin/pytest tests/unit/test_analytics.py::TestTimeseriesAnalytics::test_timeseries_success
```

## Test Configuration

**pytest.ini**
- Test discovery patterns
- Coverage thresholds (80%)
- Output formatting
- Marker definitions

**conftest.py**
- Flask app fixtures
- Database fixtures
- Redis fixtures
- Authentication fixtures
- Mock fixtures
- Sample data fixtures

**requirements-dev.txt**
- pytest and plugins
- Coverage tools
- Code quality tools (black, flake8, pylint)
- Test utilities (faker, freezegun, responses)

## Writing New Tests

### Unit Test Template

```python
import pytest
from unittest.mock import Mock, MagicMock, patch

@pytest.mark.unit
@pytest.mark.your_feature
class TestYourFeature:
    """Test suite for your feature"""

    def test_success_case(self, client, admin_token):
        """Test successful operation"""
        with patch('app_advanced.get_db_connection') as mock_db:
            # Setup mocks
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {'result': 'data'}

            mock_conn = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value = mock_conn

            # Make request
            response = client.get('/api/v1/endpoint',
                                headers={'Authorization': f'Bearer {admin_token}'})

            # Assertions
            assert response.status_code == 200
            data = response.get_json()
            assert 'result' in data

    def test_error_case(self, client):
        """Test error handling"""
        response = client.get('/api/v1/endpoint')
        assert response.status_code == 401
```

### Integration Test Template

```python
import pytest

@pytest.mark.integration
@pytest.mark.your_feature
class TestYourFeatureIntegration:
    """Integration tests for your feature"""

    def test_with_real_dependencies(self, redis_client):
        """Test with real Redis connection"""
        # Set data
        redis_client.set('test_key', 'test_value', ex=60)

        # Get data
        value = redis_client.get('test_key')
        assert value == 'test_value'

        # Clean up
        redis_client.delete('test_key')
```

## Coverage Goals

**Current Coverage**: 13.00%
**Target Coverage**: 80%+

**Coverage by Module** (as of Oct 28, 2025):
- conftest.py: 45%
- mqtt_broker.py: 18%
- rate_limiter.py: 26%
- rule_engine.py: 9%
- test_analytics.py: 21%
- test_rbac.py: 29%
- Other modules: 0-13%

**To Reach 80% Coverage**:
1. Add tests for core modules (app_advanced.py, rule_engine.py, etc.)
2. Increase integration test coverage
3. Add end-to-end tests
4. Test error paths and edge cases
5. Test all API endpoints

## Test Database Setup

```bash
# Create test database (one-time setup)
psql -h localhost -U postgres -c "CREATE DATABASE insa_iiot_test;"
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE insa_iiot_test TO iiot_user;"

# Initialize test database schema (copy from production)
pg_dump -h localhost -U iiot_user --schema-only insa_iiot | \
  psql -h localhost -U iiot_user insa_iiot_test

# Or run migration script
python3 -c "from app_advanced import init_database; init_database()"
```

## Redis Test Database

Tests use Redis database 15 (separate from production database 0):
```python
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=15,  # Test database
    decode_responses=True
)
```

## Continuous Integration

### Pre-commit Checks

```bash
# Install pre-commit hook (future)
# pre-commit install

# Run all checks manually
./venv/bin/black . --check
./venv/bin/flake8 .
./venv/bin/pylint *.py
./venv/bin/mypy *.py
./venv/bin/pytest
```

### CI/CD Pipeline (Future)

```yaml
# .github/workflows/test.yml (example)
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Troubleshooting

### Tests Fail to Collect

```bash
# Check Python path
echo $PYTHONPATH

# Reinstall dependencies
./venv/bin/pip install -r requirements-dev.txt

# Clear pytest cache
rm -rf .pytest_cache __pycache__ tests/__pycache__
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
systemctl status postgresql

# Check test database exists
psql -h localhost -U iiot_user -d insa_iiot_test -c "SELECT 1;"

# Check credentials in .env
cat .env | grep DB_
```

### Redis Connection Errors

```bash
# Check Redis is running
systemctl status redis

# Test connection
redis-cli ping

# Clear test database
redis-cli -n 15 FLUSHDB
```

### Import Errors

```bash
# Install missing dependencies
./venv/bin/pip install <package>

# Check module exists
./venv/bin/python -c "import <module>"
```

## Test Maintenance

### Regular Tasks

**Weekly**:
- Run full test suite: `pytest`
- Review coverage report: `firefox htmlcov/index.html`
- Update failing tests

**Monthly**:
- Update test dependencies: `pip install -U -r requirements-dev.txt`
- Review and remove obsolete tests
- Add tests for new features

**Per Feature**:
- Write tests before or alongside feature implementation
- Aim for 80%+ coverage per feature
- Update TESTING.md with new test info

## Performance Benchmarks

**Test Execution Time** (118 tests):
- Fast tests (<100ms): ~60 tests
- Medium tests (100ms-1s): ~40 tests
- Slow tests (>1s): ~18 tests
- **Total execution**: ~2-3 seconds (with mocks)

**Coverage Generation**:
- HTML report: ~1 second
- XML report: ~0.5 seconds
- Terminal report: ~0.1 seconds

## Best Practices

1. **Always mock external dependencies** in unit tests (database, Redis, MQTT)
2. **Use real dependencies** in integration tests
3. **Clean up after integration tests** (delete Redis keys, truncate tables)
4. **Use descriptive test names** that explain what is being tested
5. **One assertion per test** when possible (or group related assertions)
6. **Test happy path AND error paths**
7. **Use fixtures** to avoid code duplication
8. **Mark slow tests** with `@pytest.mark.slow`
9. **Keep tests independent** (no test should depend on another)
10. **Update tests when code changes**

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **Testing Flask Apps**: https://flask.palletsprojects.com/en/3.0.x/testing/
- **Mock Documentation**: https://docs.python.org/3/library/unittest.mock.html

## Next Steps

To reach 80% coverage and enable true rapid development:

### Week 1-2: Expand Test Coverage
1. Add tests for core app_advanced.py endpoints (43 endpoints)
2. Add tests for rule_engine.py (621 lines)
3. Add tests for webhook_notifier.py (394 lines)
4. Add tests for redis_cache.py (518 lines)

### Week 3-4: Integration Testing
5. Add end-to-end API tests
6. Add database integration tests
7. Add MQTT end-to-end tests
8. Performance/load testing

### Week 5-6: CI/CD & Automation
9. Set up GitHub Actions CI/CD
10. Add pre-commit hooks
11. Automated coverage reporting
12. Test result notifications

---

**Made with ❤️ by INSA Automation Corp**
**For questions**: w.aroca@insaing.com

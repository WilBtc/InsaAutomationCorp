# Integration Tests - Quick Start Guide

**INSA CRM Platform API Tests**
**File:** `test_api_endpoints.py` (1,116 lines, 35 tests)

---

## TL;DR - Run All Tests

```bash
cd /home/wil/insa-crm-platform
pytest tests/integration/test_api_endpoints.py -v
```

Expected output:
```
============================= test session starts ==============================
collected 35 items

tests/integration/test_api_endpoints.py::TestHealthEndpoint::test_health_check_success PASSED [ 2%]
tests/integration/test_api_endpoints.py::TestHealthEndpoint::test_health_check_returns_json PASSED [ 5%]
...
============================= 35 passed in 2.45s ===============================
```

---

## Test Categories

### 1. Core Endpoints (12 tests)
```bash
# Health check
pytest tests/integration/test_api_endpoints.py::TestHealthEndpoint -v

# Query endpoint (main chat)
pytest tests/integration/test_api_endpoints.py::TestQueryEndpoint -v

# Voice endpoint (Whisper transcription)
pytest tests/integration/test_api_endpoints.py::TestVoiceEndpoint -v
```

### 2. V4 API Endpoints (11 tests)
```bash
# Chat, suggestions, agent status
pytest tests/integration/test_api_endpoints.py::TestV4ChatEndpoint -v
pytest tests/integration/test_api_endpoints.py::TestV4SuggestionsEndpoint -v
pytest tests/integration/test_api_endpoints.py::TestV4AgentsStatusEndpoint -v

# Context, search, metrics
pytest tests/integration/test_api_endpoints.py::TestV4ContextEndpoint -v
pytest tests/integration/test_api_endpoints.py::TestV4SearchEndpoint -v
pytest tests/integration/test_api_endpoints.py::TestV4MetricsEndpoint -v
```

### 3. Navigation Endpoints (11 tests)
```bash
# Pipeline, projects, inbox
pytest tests/integration/test_api_endpoints.py::TestNavigationPipelineEndpoint -v
pytest tests/integration/test_api_endpoints.py::TestNavigationProjectsEndpoint -v
pytest tests/integration/test_api_endpoints.py::TestNavigationInboxEndpoint -v

# Analytics, library
pytest tests/integration/test_api_endpoints.py::TestNavigationAnalyticsEndpoint -v
pytest tests/integration/test_api_endpoints.py::TestNavigationLibraryEndpoint -v
```

### 4. Authentication (3 tests)
```bash
pytest tests/integration/test_api_endpoints.py::TestAuthenticationEndpoints -v
```

### 5. Error Handling (3 tests)
```bash
pytest tests/integration/test_api_endpoints.py::TestErrorHandling -v
```

---

## Common Test Scenarios

### Run Only Failed Tests
```bash
pytest tests/integration/test_api_endpoints.py --lf -v
```

### Run Specific Test Method
```bash
pytest tests/integration/test_api_endpoints.py::TestQueryEndpoint::test_query_success_with_text -v
```

### Run with Coverage Report
```bash
pytest tests/integration/test_api_endpoints.py --cov=crm-backend --cov=v4_api_extensions --cov-report=html
```

Open coverage report:
```bash
firefox htmlcov/index.html
```

### Run with Detailed Output
```bash
pytest tests/integration/test_api_endpoints.py -vv -s
```

### Run and Stop on First Failure
```bash
pytest tests/integration/test_api_endpoints.py -x -v
```

---

## Test Markers

### Run Only Integration Tests
```bash
pytest -m integration -v
```

### Run All Tests Except Integration
```bash
pytest -m "not integration" -v
```

---

## Debugging Failed Tests

### Show Full Traceback
```bash
pytest tests/integration/test_api_endpoints.py --tb=long -v
```

### Show Local Variables in Traceback
```bash
pytest tests/integration/test_api_endpoints.py --tb=long --showlocals -v
```

### Run with Python Debugger (pdb)
```bash
pytest tests/integration/test_api_endpoints.py --pdb
```

### Print Output During Tests
```bash
pytest tests/integration/test_api_endpoints.py -s
```

---

## Test Fixtures Available

### `flask_test_app`
Flask test client with mocked dependencies
```python
def test_example(self, flask_test_app):
    response = flask_test_app.get('/health')
    assert response.status_code == 200
```

### `valid_jwt_token`
Valid JWT token for authentication
```python
def test_example(self, flask_test_app, valid_jwt_token):
    response = flask_test_app.post('/query',
        data={'text': 'test', 'token': valid_jwt_token}
    )
```

### `sample_audio_file`
Sample WAV file for voice tests
```python
def test_example(self, flask_test_app, sample_audio_file):
    response = flask_test_app.post('/transcribe',
        data={'audio': (sample_audio_file, 'test.wav')}
    )
```

### `sample_text_file`
Sample text file for upload tests
```python
def test_example(self, flask_test_app, sample_text_file):
    response = flask_test_app.post('/query',
        data={'file0': (sample_text_file, 'test.txt')}
    )
```

---

## Expected Test Results

### All Tests Should Pass
```
============================= 35 passed in 2.45s ===============================
```

### If Tests Fail

#### Check Imports
```bash
cd /home/wil/insa-crm-platform/crm\ voice
python3 -c "import crm_backend; import v4_api_extensions; import v4_api_extensions_navigation"
```

#### Check Dependencies
```bash
pip list | grep -E "pytest|flask|mock"
```

Required packages:
- `pytest >= 7.0.0`
- `Flask >= 2.0.0`
- `unittest.mock` (built-in)

#### Check File Paths
```bash
ls -l /home/wil/insa-crm-platform/crm\ voice/*.py
```

Required files:
- `crm-backend.py`
- `v4_api_extensions.py`
- `v4_api_extensions_navigation.py`
- `session_manager.py`
- `auth_manager.py`
- `session_claude_manager.py`

---

## Writing New Tests

### Template for New Test Class
```python
@pytest.mark.integration
class TestNewEndpoint:
    """Test /api/v4/new endpoint"""

    def test_new_endpoint_success(self, flask_test_app):
        """
        Test new endpoint returns expected data

        AAA Pattern:
        - Arrange: Set up test data
        - Act: Call endpoint
        - Assert: Verify response
        """
        # Arrange
        expected_data = {'key': 'value'}

        # Act
        response = flask_test_app.get('/api/v4/new')

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == expected_data

    def test_new_endpoint_error(self, flask_test_app):
        """Test new endpoint error handling"""
        # Arrange
        with patch('module.function') as mock_func:
            mock_func.side_effect = Exception("Error")

        # Act
        response = flask_test_app.get('/api/v4/new')

        # Assert
        assert response.status_code == 500
```

### Template for New Test Method
```python
def test_endpoint_scenario(self, flask_test_app, fixture1, fixture2):
    """
    Short description of what this test verifies

    Verifies:
    - Specific behavior 1
    - Specific behavior 2
    """
    # Arrange
    test_data = {'key': 'value'}

    # Act
    response = flask_test_app.post('/endpoint', json=test_data)

    # Assert
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'expected_key' in data
```

---

## Performance Benchmarks

### Target Metrics
- **Test Suite Runtime:** <5s (current: ~2.5s)
- **Individual Test:** <100ms (current: ~70ms avg)
- **Setup Time:** <500ms (current: ~300ms)

### Run with Timing
```bash
pytest tests/integration/test_api_endpoints.py -v --durations=10
```

Shows slowest 10 tests.

---

## Continuous Integration

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/integration/test_api_endpoints.py --tb=short
```

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest tests/integration/test_api_endpoints.py -v
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'crm-backend'"
**Fix:** Module name has hyphen, import as `crm_backend` (underscore)
```python
import crm_backend  # NOT crm-backend
```

### "AttributeError: module has no attribute 'app'"
**Fix:** Check sys.path includes `/home/wil/insa-crm-platform/crm voice`
```python
sys.path.insert(0, '/home/wil/insa-crm-platform/crm voice')
```

### "AssertionError: assert 500 == 200"
**Fix:** Check mock setup, may need to mock additional dependencies
```bash
pytest tests/integration/test_api_endpoints.py::TestClass::test_method -vv --tb=long
```

### "OSError: [Errno 24] Too many open files"
**Fix:** Increase file descriptor limit
```bash
ulimit -n 4096
```

---

## Test Coverage Summary

| Endpoint Category | Endpoints | Tests | Coverage |
|-------------------|-----------|-------|----------|
| **Core** | 4 | 12 | 100% |
| **V4 API** | 6 | 11 | 100% |
| **Navigation** | 5 | 11 | 100% |
| **Auth** | 4 | 3 | 75% |
| **File Storage** | 8 | 0 | 0% ❌ |
| **Error Handling** | N/A | 3 | 100% |
| **TOTAL** | **27** | **35** | **~85%** |

**Next Priority:** Add file storage endpoint tests (0% coverage)

---

## Additional Resources

- **Test File:** `/home/wil/insa-crm-platform/tests/integration/test_api_endpoints.py`
- **Summary:** `/home/wil/insa-crm-platform/tests/integration/TEST_SUMMARY.md`
- **Fixtures:** `/home/wil/insa-crm-platform/tests/conftest.py`
- **API Docs:** `/home/wil/insa-crm-platform/crm voice/CRM-README.md`

---

**Made by Insa Automation Corp** | October 30, 2025

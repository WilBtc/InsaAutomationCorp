# INSA CRM Platform - Security Audit Remediation Plan
**Date:** October 30, 2025 17:00 UTC
**Status:** 🔴 14 Tasks Pending
**Priority:** HIGH - Security & Code Quality Improvements
**Timeline:** 6 weeks to completion

---

## 📋 Executive Summary

Following the comprehensive security audit, we've identified 15 critical issues (excluding test-only hardcoded credentials). This plan outlines a logical, prioritized approach to remediate all findings.

**Risk Level:** 🔴 HIGH (6.75/10)
**Test Coverage:** 0% → Target: 80%
**Timeline:** 6 weeks (3 phases)
**Effort:** ~120 hours total

---

## 🎯 Implementation Strategy

### Phase 1: Critical Security Fixes (Week 1) - 8 hours
**Objective:** Eliminate immediate security risks

1. ✅ Remove SSL keys from git history (30 min)
2. ✅ Update .gitignore (15 min)
3. ✅ Create .env.example (30 min)
4. ✅ Set up pytest infrastructure (2 hours)
5. ✅ Fix 10 bare exception handlers (3 hours)
6. ✅ Document all environment variables (1.5 hours)

### Phase 2: Code Quality & Testing (Weeks 2-3) - 40 hours
**Objective:** Establish testing foundation and improve logging

7. ✅ Replace print() with logger (top 5 files) (8 hours)
8. ✅ Write authentication tests (8 hours)
9. ✅ Write API endpoint tests (8 hours)
10. ✅ Achieve 20% test coverage baseline (16 hours)

### Phase 3: Production Hardening (Weeks 4-6) - 72 hours
**Objective:** Production-ready deployment infrastructure

11. ✅ Fix 16 command injection risks (8 hours)
12. ✅ Move hardcoded URLs to env vars (4 hours)
13. ✅ Set up Alembic migrations (6 hours)
14. ✅ Refactor large files (16 hours)
15. ✅ Set up CI/CD pipeline (8 hours)
16. ✅ Add pre-commit hooks (2 hours)
17. ✅ Achieve 80% test coverage (28 hours)

---

## 📊 Task Details & Priorities

### 🔴 CRITICAL - Phase 1 (This Week)

#### Task 1: Remove SSL Private Keys from Git History
**Priority:** 🔴 CRITICAL
**Effort:** 30 minutes
**Files:** `crm voice/ssl/cert.pem`, `crm voice/ssl/key.pem`

**Why Critical:**
- Private keys should NEVER be in version control
- Security audit failure
- Compliance risk (PCI-DSS, SOC 2)

**Implementation:**
```bash
# Remove SSL files from entire git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch 'crm voice/ssl/*'" \
  --prune-empty --tag-name-filter cat -- --all

# Force push to remote
git push origin --force --all
git push origin --force --tags

# Clean up local references
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

**Verification:**
```bash
# Verify keys are gone from history
git log --all --full-history -- "crm voice/ssl/*"
# Should return nothing
```

---

#### Task 2: Update .gitignore
**Priority:** 🔴 CRITICAL
**Effort:** 15 minutes
**File:** `.gitignore`

**Add to .gitignore:**
```gitignore
# SSL Certificates & Private Keys
*.pem
*.key
*.crt
*.p12
*.pfx
ssl/
certs/

# Secrets & Credentials
secrets/
.env
.env.local
.env.production
credentials/
*.credentials

# Database Dumps
*.sql.gz
*.dump
*.backup
backups/

# Temporary Files
*.tmp
*.temp
.DS_Store
```

---

#### Task 3: Create .env.example
**Priority:** 🔴 CRITICAL
**Effort:** 30 minutes
**File:** `.env.example`

**Document All Required Variables:**
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/insa_crm
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=insa_crm
POSTGRES_USER=insa_user
POSTGRES_PASSWORD=change_me_in_production

# Application Security
SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_ACCESS_TOKEN_EXPIRES=3600

# External Services
ERPNEXT_API_URL=http://localhost:9000
ERPNEXT_USERNAME=administrator
ERPNEXT_PASSWORD=change_me

INVENTREE_URL=http://localhost:9600
INVENTREE_API_TOKEN=generate_in_inventree_settings

MAUTIC_URL=http://localhost:9700
MAUTIC_API_TOKEN=generate_in_mautic_settings

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# SMTP Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM=noreply@insaautomation.com
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=app_specific_password

# Vector Database
QDRANT_HOST=100.107.50.52
QDRANT_PORT=6333

# MinIO Object Storage
MINIO_ENDPOINT=172.17.0.3:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=change_me

# Claude AI
CLAUDE_API_KEY=optional_for_subprocess_mode

# Monitoring
PROMETHEUS_PORT=9091
GRAFANA_URL=http://localhost:3002

# Feature Flags
ENABLE_VOICE_INPUT=true
ENABLE_RAG_SEARCH=true
ENABLE_AUTO_HEALING=true
```

**Generate Secure Values:**
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32
```

---

#### Task 4: Set Up pytest Infrastructure
**Priority:** 🔴 CRITICAL
**Effort:** 2 hours
**Impact:** Foundation for all testing

**Create pytest.ini:**
```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output formatting
addopts =
    --verbose
    --color=yes
    --strict-markers
    --tb=short
    --cov=core
    --cov=crm voice
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=20

# Coverage exclusions
[coverage:run]
omit =
    */tests/*
    */venv/*
    */migrations/*
    */__pycache__/*
    setup.py

# Markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    security: marks tests as security tests
```

**Create Directory Structure:**
```bash
mkdir -p tests/{unit,integration,fixtures}
touch tests/__init__.py
touch tests/conftest.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

**Create conftest.py:**
```python
"""pytest configuration and fixtures"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def client():
    """Flask test client"""
    from crm_voice.crm-backend import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def db_session():
    """Database session for testing"""
    # TODO: Implement database session fixture
    pass

@pytest.fixture
def mock_claude():
    """Mock Claude Code subprocess"""
    # TODO: Implement Claude mock
    pass
```

**Install Test Dependencies:**
```bash
cd "/home/wil/insa-crm-platform/crm voice"
./venv/bin/pip install pytest pytest-cov pytest-mock pytest-asyncio
```

---

#### Task 5: Fix 10 Bare Exception Handlers
**Priority:** 🔴 CRITICAL
**Effort:** 3 hours (20 min per file)
**Impact:** Prevents silent failures

**Files to Fix:**
1. `crm voice/agent_retry.py`
2. `core/agents/business_card_pipeline.py` (2 instances)
3. `crm voice/mcp_client_simple.py` (2 instances)
4. `core/agents/integrated_healing_system.py`
5. `mcp-servers/n8n-admin/server.py`
6. `crm voice/crm-backend.py`

**Pattern to Replace:**
```python
# ❌ BEFORE (Silent failure)
try:
    response_data = json.loads(result.stdout)
except:
    pass

# ✅ AFTER (Proper error handling)
try:
    response_data = json.loads(result.stdout)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse JSON response: {e}")
    response_data = {}
except Exception as e:
    logger.error(f"Unexpected error parsing response: {e}")
    raise
```

**Implementation Checklist:**
- [ ] agent_retry.py - Line TBD
- [ ] business_card_pipeline.py - 2 instances
- [ ] mcp_client_simple.py - 2 instances
- [ ] integrated_healing_system.py - Line TBD
- [ ] n8n-admin/server.py - Line TBD
- [ ] crm-backend.py - Line TBD

---

### 🟠 HIGH PRIORITY - Phase 2 (Weeks 2-3)

#### Task 6: Replace print() with logger Calls
**Priority:** 🟠 HIGH
**Effort:** 8 hours
**Impact:** Production-grade logging

**Top 5 Files to Fix:**
1. `setup_minio_buckets.py` - 47 print statements
2. `crm voice/audit_system.py` - 45 print statements
3. `scripts/analyze_ideal_customer.py` - 45 print statements
4. `scripts/ingest_historical_projects.py` - 36 print statements
5. `core/agents/task_orchestration_agent.py` - 30 print statements

**Total:** 203 print statements → logger calls

**Pattern:**
```python
# ❌ BEFORE
print(f"Processing {item}...")
print("ERROR: Failed to process")

# ✅ AFTER
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing {item}...")
logger.error("Failed to process", exc_info=True)
```

**Logging Levels:**
- `logger.debug()` - Detailed diagnostic info
- `logger.info()` - General informational messages
- `logger.warning()` - Warning messages (non-critical)
- `logger.error()` - Error messages (critical)
- `logger.critical()` - System failure messages

---

#### Task 7: Write Authentication Tests
**Priority:** 🟠 HIGH
**Effort:** 8 hours
**Files:** `tests/unit/test_auth.py`, `tests/integration/test_auth_api.py`

**Test Coverage:**
```python
# tests/unit/test_auth.py
def test_password_hashing():
    """Test bcrypt password hashing"""
    pass

def test_jwt_token_generation():
    """Test JWT token generation"""
    pass

def test_jwt_token_validation():
    """Test JWT token validation"""
    pass

def test_token_expiration():
    """Test JWT token expiration"""
    pass

def test_rate_limiting():
    """Test 5 login attempts/minute limit"""
    pass

# tests/integration/test_auth_api.py
def test_login_success(client):
    """Test successful login"""
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'testpass'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    pass

def test_login_rate_limit_exceeded(client):
    """Test rate limit on login endpoint"""
    pass
```

**Target Coverage:** 90% of authentication module

---

#### Task 8: Write API Endpoint Tests
**Priority:** 🟠 HIGH
**Effort:** 8 hours
**Files:** `tests/integration/test_api_endpoints.py`

**Endpoints to Test:**
```python
# /query endpoint
def test_query_endpoint_success(client):
    """Test successful query"""
    pass

def test_query_endpoint_timeout(client):
    """Test query timeout (540s)"""
    pass

# /chat endpoint
def test_chat_endpoint_session_persistence(client):
    """Test session persistence (5 hours)"""
    pass

# /api/v4/* endpoints (7 total)
def test_v4_chat_endpoint(client):
    pass

def test_v4_suggestions_endpoint(client):
    pass

def test_v4_agents_status_endpoint(client):
    pass

def test_v4_active_deal_endpoint(client):
    pass

def test_v4_search_endpoint(client):
    pass

def test_v4_metrics_endpoint(client):
    pass
```

---

#### Task 9: Achieve 20% Test Coverage Baseline
**Priority:** 🟠 HIGH
**Effort:** 16 hours
**Target:** 8,631 lines covered (43,158 * 0.20)

**Coverage Breakdown:**
- Authentication module: 90% coverage (4 hours)
- API endpoints: 80% coverage (8 hours)
- Database models: 50% coverage (2 hours)
- Utility functions: 30% coverage (2 hours)

**Run Coverage Report:**
```bash
pytest --cov=core --cov=crm_voice --cov-report=html
open htmlcov/index.html
```

---

### 🟡 MEDIUM PRIORITY - Phase 3 (Weeks 4-6)

#### Task 10: Fix 16 Command Injection Risks
**Priority:** 🟡 MEDIUM
**Effort:** 8 hours
**Files:** 16 files using subprocess with shell=True

**Pattern to Replace:**
```python
# ❌ BEFORE (Command injection risk)
import subprocess
auth_cmd = f"curl -X POST -d '{{\"usr\": \"{username}\"}}' http://api/login"
subprocess.run(auth_cmd, shell=True)

# ✅ AFTER (Safe - use requests library)
import requests
response = requests.post('http://api/login', json={'usr': username})

# OR if subprocess is required (Safe - use shlex)
import subprocess
import shlex
cmd = ['curl', '-X', 'POST', '-d', f'{{"usr": "{shlex.quote(username)}"}}', 'http://api/login']
subprocess.run(cmd, shell=False)
```

**Files to Fix:**
1. `mcp-servers/erpnext-crm/server.py` (highest priority)
2. 15 other files using subprocess

---

#### Task 11: Move Hardcoded URLs to Environment Variables
**Priority:** 🟡 MEDIUM
**Effort:** 4 hours
**Files:** 19 files

**Hardcoded URLs to Replace:**
- `http://100.100.101.1:9000` → `${ERPNEXT_API_URL}`
- `http://100.100.101.1:9600` → `${INVENTREE_URL}`
- `http://100.100.101.1:9700` → `${MAUTIC_URL}`
- `http://100.107.50.52` → `${QDRANT_HOST}`

**Pattern:**
```python
# ❌ BEFORE
ERPNEXT_URL = "http://100.100.101.1:9000"

# ✅ AFTER
import os
ERPNEXT_URL = os.getenv('ERPNEXT_API_URL', 'http://localhost:9000')
```

---

#### Task 12: Set Up Alembic Database Migrations
**Priority:** 🟡 MEDIUM
**Effort:** 6 hours
**Impact:** Reproducible database state

**Implementation:**
```bash
# Initialize Alembic
cd "/home/wil/insa-crm-platform/crm voice"
./venv/bin/alembic init alembic

# Configure alembic.ini
# Set sqlalchemy.url to DATABASE_URL

# Create initial migration
./venv/bin/alembic revision --autogenerate -m "Initial schema"

# Apply migration
./venv/bin/alembic upgrade head
```

**Migrate Existing SQL Files:**
- Convert `008_*.sql` → Alembic migration
- Convert `009_*.sql` → Alembic migration
- Convert `010_*.sql` → Alembic migration
- Convert `011_*.sql` → Alembic migration
- Convert `012_*.sql` → Alembic migration

---

#### Task 13: Refactor Large Files
**Priority:** 🟡 MEDIUM
**Effort:** 16 hours (4 hours per file)
**Files:** 4 largest files

**1. integrated_healing_system.py (2,236 lines)**
Break into:
- `healing/pattern_recognition.py` - IntelligentLogAnalyzer (200 lines)
- `healing/context_awareness.py` - ServiceClassifier (150 lines)
- `healing/learning_system.py` - LearningDatabase (300 lines)
- `healing/metacognition.py` - MetacognitiveAgent (150 lines)
- `healing/orchestrator.py` - Main healing logic (500 lines)

**2. erpnext-crm/server.py (1,667 lines)**
Break into:
- `erpnext/auth.py` - Authentication logic
- `erpnext/leads.py` - Lead management
- `erpnext/opportunities.py` - Opportunity management
- `erpnext/quotations.py` - Quotation management
- `erpnext/server.py` - MCP server (300 lines)

**3. crm-backend.py (1,436 lines)**
Break into:
- `api/auth.py` - Auth endpoints
- `api/chat.py` - Chat endpoints
- `api/v4_extensions.py` - V4 endpoints (already exists)
- `app.py` - Flask app initialization (200 lines)

**4. n8n-admin/server.py (1,261 lines)**
Break into:
- `n8n/workflows.py` - Workflow management
- `n8n/executions.py` - Execution management
- `n8n/credentials.py` - Credential management
- `n8n/server.py` - MCP server (300 lines)

---

#### Task 14: Set Up GitHub Actions CI/CD
**Priority:** 🟡 MEDIUM
**Effort:** 8 hours
**Files:** `.github/workflows/ci.yml`, `.github/workflows/security.yml`

**Create .github/workflows/ci.yml:**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: pytest --cov --cov-fail-under=20

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Run Black
        run: |
          pip install black
          black --check .

      - name: Run Ruff
        run: |
          pip install ruff
          ruff check .

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r . -f json -o bandit-report.json

      - name: Run Safety
        run: |
          pip install safety
          safety check --json
```

---

#### Task 15: Add Pre-commit Hooks
**Priority:** 🟡 MEDIUM
**Effort:** 2 hours
**File:** `.pre-commit-config.yaml`

**Create .pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: [-r, ., -f, json]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: detect-private-key
```

**Install:**
```bash
pip install pre-commit
pre-commit install
```

---

#### Task 16: Achieve 80% Test Coverage
**Priority:** 🟡 MEDIUM
**Effort:** 28 hours
**Target:** 34,526 lines covered (43,158 * 0.80)

**Coverage by Module:**
- Authentication: 95% (already at 90%)
- API endpoints: 90% (already at 80%)
- Database models: 85%
- Healing system: 80%
- MCP servers: 75%
- Utility functions: 70%

**Weekly Progress:**
- Week 4: 20% → 40% (8,631 → 17,263 lines)
- Week 5: 40% → 60% (17,263 → 25,895 lines)
- Week 6: 60% → 80% (25,895 → 34,526 lines)

---

## 📈 Progress Tracking

### Week 1: Critical Security (8 hours)
- [ ] Day 1: Remove SSL keys + Update .gitignore (1 hour)
- [ ] Day 2: Create .env.example + Document variables (2 hours)
- [ ] Day 3-4: Set up pytest infrastructure (2 hours)
- [ ] Day 5: Fix bare exception handlers (3 hours)

### Week 2-3: Code Quality & Testing (40 hours)
- [ ] Week 2: Replace print() statements (8 hours)
- [ ] Week 2: Write auth tests (8 hours)
- [ ] Week 3: Write API tests (8 hours)
- [ ] Week 3: Achieve 20% coverage (16 hours)

### Week 4-6: Production Hardening (72 hours)
- [ ] Week 4: Fix command injection (8 hours)
- [ ] Week 4: Move URLs to env vars (4 hours)
- [ ] Week 4: Set up Alembic (6 hours)
- [ ] Week 4-5: Refactor large files (16 hours)
- [ ] Week 5: Set up CI/CD (8 hours)
- [ ] Week 5: Add pre-commit hooks (2 hours)
- [ ] Week 5-6: Achieve 80% coverage (28 hours)

---

## 🎯 Success Metrics

| Metric | Current | Week 1 | Week 3 | Week 6 |
|--------|---------|--------|--------|--------|
| **Test Coverage** | 0% | 5% | 20% | 80% |
| **Risk Level** | 6.75 | 5.5 | 4.0 | 2.5 |
| **print() statements** | 922 | 722 | 200 | 0 |
| **Bare exceptions** | 10 | 0 | 0 | 0 |
| **SSL in git** | Yes | No | No | No |
| **CI/CD Pipeline** | No | No | No | Yes |
| **Migration System** | Manual | Manual | Manual | Alembic |

---

## 🔧 Tools & Dependencies

### Required Tools
```bash
# Testing
pip install pytest pytest-cov pytest-mock pytest-asyncio

# Code Quality
pip install black ruff bandit safety pip-audit

# Pre-commit
pip install pre-commit

# Database Migrations
pip install alembic

# Security Scanning
pip install safety bandit
```

---

## 📚 Documentation Updates

After each phase, update:
- [ ] README.md - Add testing instructions
- [ ] CLAUDE.md - Update status
- [ ] TESTING.md - Document test strategy (new file)
- [ ] SECURITY.md - Document security practices (new file)
- [ ] CONTRIBUTING.md - Add development guidelines (new file)

---

## 🎓 Learning Resources

- **pytest:** https://docs.pytest.org
- **Alembic:** https://alembic.sqlalchemy.org
- **GitHub Actions:** https://docs.github.com/actions
- **pre-commit:** https://pre-commit.com
- **OWASP Top 10:** https://owasp.org/Top10

---

**Made by Insa Automation Corp**
**Lead Engineer:** Wil Aroca + Claude Code
**Plan Created:** October 30, 2025 17:00 UTC
**Status:** Ready for implementation

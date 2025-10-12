# Multi-Tenant SaaS SOC Architecture
**Project**: Insa Automation Corp SecureOps Platform
**Date**: 2025-10-11
**Version**: 1.0
**Status**: Design Phase

---

## Executive Summary

This document defines the complete architecture for **Insa Automation Corp's Multi-Tenant Security-as-a-Service (SecaaS) Platform**, transforming INSA's internal security capabilities into a scalable, white-labeled SaaS offering.

**Platform Name**: **Insa SecureOps Platform**
**Target Market**: SMBs to Enterprise clients needing 24/7 security monitoring, vulnerability management, and compliance reporting
**Deployment**: iac1 (100.100.101.1) as primary SaaS platform
**Reference Architecture**: netg (100.121.213.50) internal SOC

---

## Architecture Overview

### High-Level Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     INSA AUTOMATION CORP NETWORK                            │
│                        (Tailscale VPN: 100.x.x.x)                          │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
┌─────────▼──────────┐    ┌────────▼──────────┐   ┌─────────▼──────────┐
│   netg (Internal)  │    │  iac1 (SaaS)      │   │  Client Networks   │
│  100.121.213.50    │◄───┤  100.100.101.1    │◄──┤  (External)        │
│                    │    │                   │   │                    │
│ ┌────────────────┐ │    │ ┌───────────────┐│   │ ┌────────────────┐ │
│ │ Wazuh Manager  │ │    │ │ DefectDojo    ││   │ │ Client Servers │ │
│ │ (INSA Internal)│ │    │ │ (Multi-Tenant)││   │ │ w/ Wazuh Agent │ │
│ └────────────────┘ │    │ └───────────────┘│   │ └────────────────┘ │
│                    │    │                   │   │                    │
│ ┌────────────────┐ │    │ ┌───────────────┐│   │ ┌────────────────┐ │
│ │   Greenbone    │ │    │ │   GroupMQ     ││   │ │ Client Apps    │ │
│ │   /OpenVAS     │ │    │ │  (Msg Queue)  ││   │ │                │ │
│ └────────────────┘ │    │ └───────────────┘│   │ └────────────────┘ │
│                    │    │                   │   │                    │
│ ┌────────────────┐ │    │ ┌───────────────┐│   └────────────────────┘
│ │  Suricata IDS  │ │    │ │ AI Triage     ││           │
│ │                │ │    │ │ Engine        ││           │
│ └────────────────┘ │    │ └───────────────┘│           │
│                    │    │                   │           │
│ ┌────────────────┐ │    │ ┌───────────────┐│           │
│ │ Custom MCP     │ │    │ │ White-Labeled ││           │
│ │ Servers        │ │    │ │ MCP Servers   ││           │
│ └────────────────┘ │    │ └───────────────┘│           │
│                    │    │                   │           │
│ Agents:            │    │ Services:         │           │
│  - netg (self)     │    │  - Client Portal  │           │
│  - iac1 ◄──────────┼────┤  - API Gateway    │           │
│  - LU1             │    │  - Scanner Pool   │           │
│  - ERP             │    │  - Report Gen     │           │
│                    │    │  - Billing        │           │
└────────────────────┘    └───────────────────┘           │
          │                         │                      │
          │                         │                      │
          └───── Threat Intel ──────┴──────────────────────┘
                Configuration Sync
                Learning Patterns
```

---

## Core Components

### 1. iac1 SaaS Platform Components

```yaml
Server: iac1 (100.100.101.1)
OS: Ubuntu (same as netg)
Role: Multi-Tenant SaaS Platform
Hostname: iac1.insa-automation.com (public DNS)
```

#### Application Stack

```
┌─────────────────────────────────────────────────────────┐
│              Load Balancer / Reverse Proxy              │
│         (Traefik or Nginx with SSL Termination)         │
│          portal.insa-automation.com (443/80)            │
└───────────┬─────────────────────────────────────────────┘
            │
            ├─────► /api/v2/*        → API Gateway
            ├─────► /dashboard/*     → Client Portal (React/Vue)
            ├─────► /defectdojo/*    → DefectDojo (White-Labeled)
            └─────► /docs/*          → API Documentation

┌────────────────────────────────────────────────────────────┐
│                      API Gateway                           │
│   - Authentication (JWT, API Keys)                         │
│   - Rate Limiting (per client)                             │
│   - Request Routing                                        │
│   - Logging & Audit                                        │
└──────────┬────────────────────────────────────────────────┘
           │
           ├─────► DefectDojo API (findings, products, scans)
           ├─────► Scanner API (start scans, get status)
           ├─────► Reporting API (generate reports)
           ├─────► Billing API (usage, invoices)
           └─────► User Management API (CRUD users)

┌────────────────────────────────────────────────────────────┐
│                      DefectDojo Core                       │
│  - Products (one per client)                               │
│  - Findings (isolated by product)                          │
│  - Engagements (scan campaigns)                            │
│  - Tests (individual scans)                                │
│  - White-Labeled UI                                        │
└──────────┬────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                      │
│  - Row-Level Security (RLS) enabled                        │
│  - Client ID on all tables                                 │
│  - Encrypted at rest (LUKS/dm-crypt)                       │
│  - Continuous WAL archiving                                │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                     GroupMQ (Message Queue)                │
│  - Scan job distribution                                   │
│  - Real-time notifications                                 │
│  - AI triage queue                                         │
│  - Client onboarding workflow                              │
│  - Audit event stream                                      │
│  GitHub: https://github.com/Openpanel-dev/groupmq.git     │
└──────────┬────────────────────────────────────────────────┘
           │
           ├─────► Scanner Workers (VM pool)
           ├─────► AI Triage Workers (GPU optional)
           ├─────► Notification Service (email, webhooks, SMS)
           └─────► Audit Logger (append-only audit log)

┌────────────────────────────────────────────────────────────┐
│                    AI Triage Engine                        │
│  - Claude Code subprocess (local, zero API cost)           │
│  - EPSS integration                                        │
│  - Learning database (SQLite per client)                   │
│  - Confidence scoring                                      │
│  - Bulk triage capabilities                                │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                   Scanner Pool (Workers)                   │
│  - Trivy (container scanning)                              │
│  - OWASP ZAP (web app scanning)                            │
│  - Nmap (network discovery)                                │
│  - Nikto (web server scanning)                             │
│  - Custom scanners (optional)                              │
│  - Subscribes to GroupMQ scan queue                        │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                    MCP Servers (White-Labeled)             │
│  insa-defectdojo-mcp:                                      │
│    - 8 tools (get_findings, triage_finding, etc)           │
│    - Per-client API key filtering                          │
│  insa-scanner-mcp:                                         │
│    - Start scans                                           │
│    - Check scan status                                     │
│    - Get scan results                                      │
│  insa-reporting-mcp:                                       │
│    - Generate reports                                      │
│    - Schedule reports                                      │
│    - Download reports                                      │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                   Monitoring & Observability               │
│  - Prometheus (metrics collection)                         │
│  - Grafana (dashboards)                                    │
│  - Loki (log aggregation)                                  │
│  - Wazuh Agent (reports to netg)                           │
│  - Health checks (every 60 seconds)                        │
│  - Status page: https://status.insa-automation.com         │
└────────────────────────────────────────────────────────────┘
```

---

### 2. Data Model - Multi-Tenancy

#### Option A: Shared Database with Row-Level Security ⭐ **Recommended for Launch**

```sql
-- PostgreSQL Schema with Multi-Tenancy

-- Clients table (master tenant list)
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'client_acme'
    company_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',  -- active, suspended, cancelled
    tier VARCHAR(20) NOT NULL,  -- basic, pro, enterprise
    billing_email VARCHAR(255),
    api_key_hash VARCHAR(255) UNIQUE,  -- bcrypt hash
    settings JSONB  -- client-specific settings
);

-- Users table (client users)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) REFERENCES clients(client_id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- client_admin, client_user, client_readonly
    mfa_enabled BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- DefectDojo Products (one per client)
CREATE TABLE defectdojo_products (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) REFERENCES clients(client_id),
    product_name VARCHAR(255) NOT NULL,
    defectdojo_product_id INTEGER NOT NULL,  -- ID in DefectDojo
    created_at TIMESTAMP DEFAULT NOW()
);

-- Findings table (RLS enforced)
CREATE TABLE findings (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) REFERENCES clients(client_id),  -- CRITICAL for isolation
    defectdojo_finding_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL,
    cwe INTEGER,
    cvss NUMERIC(3,1),
    epss_score NUMERIC(5,4),
    ai_triage_status VARCHAR(50),
    ai_confidence NUMERIC(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable Row-Level Security on findings
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their client's findings
CREATE POLICY client_isolation_policy ON findings
    FOR ALL
    TO PUBLIC
    USING (client_id = current_setting('app.current_client_id')::text);

-- Before each API request, set the client context
-- In application code (Python example):
-- conn.execute("SET LOCAL app.current_client_id = %s", (client_id,))

-- Scans table
CREATE TABLE scans (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) REFERENCES clients(client_id),
    scan_type VARCHAR(50) NOT NULL,  -- nessus, trivy, zap, etc.
    target VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- queued, running, completed, failed
    findings_count INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
CREATE POLICY client_isolation_policy ON scans
    FOR ALL TO PUBLIC
    USING (client_id = current_setting('app.current_client_id')::text);

-- Usage metrics table (for billing)
CREATE TABLE usage_metrics (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) REFERENCES clients(client_id),
    metric_type VARCHAR(50) NOT NULL,  -- api_calls, scans, storage_gb, assets
    metric_value INTEGER NOT NULL,
    recorded_at DATE NOT NULL,
    UNIQUE(client_id, metric_type, recorded_at)
);

-- Audit log table (no RLS - admins need visibility)
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50),
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,  -- login, view_finding, triage_finding, etc.
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    result VARCHAR(20) NOT NULL,  -- success, failure
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_findings_client_id ON findings(client_id);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_status ON findings(status);
CREATE INDEX idx_scans_client_id ON scans(client_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_audit_log_client_id ON audit_log(client_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- Example query (automatically filtered by RLS):
-- SET app.current_client_id = 'client_acme';
-- SELECT * FROM findings WHERE severity = 'Critical';
-- Result: Only returns client_acme's critical findings
```

---

### 3. Authentication & Authorization Architecture

```yaml
Authentication Flow:

1. Client Login (Web UI):
   User enters email + password
   ↓
   API: POST /api/v2/auth/login
   {
     "email": "admin@acme.com",
     "password": "***",
     "mfa_code": "123456"  # if MFA enabled
   }
   ↓
   Backend:
     - Validate credentials
     - Check MFA if enabled
     - Query client_id from users table
     - Generate JWT with claims:
       {
         "user_id": 42,
         "client_id": "client_acme",
         "role": "client_admin",
         "exp": 1697046000  # 30 min expiry
       }
     - Sign JWT with secret key
   ↓
   Response:
   {
     "access_token": "eyJhbGci....",
     "refresh_token": "eyJhbGci....",
     "expires_in": 1800,
     "token_type": "Bearer"
   }

2. API Key Authentication (Programmatic):
   Client sends API key in header:
     Authorization: Token dd_api_key_acme_abc123

   Backend:
     - Hash API key
     - Look up client_id in clients table
     - Verify client status = 'active'
     - Check rate limit for this client
     - Set app.current_client_id = 'client_acme'

3. SSO/SAML Authentication (Enterprise tier):
   User clicks "Login with Okta"
   ↓
   Redirect to Okta IdP
   ↓
   User authenticates at Okta
   ↓
   SAML assertion sent to callback URL
   ↓
   Backend:
     - Validate SAML assertion
     - Extract email from assertion
     - Look up user in database
     - Create session / JWT
     - Redirect to dashboard

Authorization (RBAC):

Roles:
  - platform_admin: INSA staff (god mode)
  - client_owner: Full access to client's org
  - client_admin: Manage users, view/edit findings
  - client_analyst: View/triage findings only
  - client_readonly: View findings only
  - client_api: API access with custom permissions

Permissions Matrix:

| Action                  | platform_admin | client_owner | client_admin | client_analyst | client_readonly | client_api |
|-------------------------|----------------|--------------|--------------|----------------|-----------------|------------|
| View own findings       | ✅             | ✅           | ✅           | ✅             | ✅              | ✅ (if scope) |
| View other client findings | ✅          | ❌           | ❌           | ❌             | ❌              | ❌         |
| Triage findings         | ✅             | ✅           | ✅           | ✅             | ❌              | ✅ (if scope) |
| Close findings          | ✅             | ✅           | ✅           | ✅             | ❌              | ✅ (if scope) |
| Delete findings         | ✅             | ✅           | ✅           | ❌             | ❌              | ❌         |
| Start scans             | ✅             | ✅           | ✅           | ✅             | ❌              | ✅ (if scope) |
| View reports            | ✅             | ✅           | ✅           | ✅             | ✅              | ✅ (if scope) |
| Generate reports        | ✅             | ✅           | ✅           | ✅             | ❌              | ✅ (if scope) |
| Manage users            | ✅             | ✅           | ✅           | ❌             | ❌              | ❌         |
| View billing            | ✅             | ✅           | ❌           | ❌             | ❌              | ❌         |
| Manage API keys         | ✅             | ✅           | ✅           | ❌             | ❌              | ❌         |
| Configure integrations  | ✅             | ✅           | ✅           | ❌             | ❌              | ❌         |
| View all clients        | ✅             | ❌           | ❌           | ❌             | ❌              | ❌         |
| Suspend clients         | ✅             | ❌           | ❌           | ❌             | ❌              | ❌         |

Implementation (Python/Django example):
  from functools import wraps

  def require_permission(permission):
      def decorator(func):
          @wraps(func)
          def wrapper(request, *args, **kwargs):
              # Extract JWT or API key
              token = request.headers.get('Authorization')
              user = authenticate(token)

              # Check permission
              if not user.has_permission(permission):
                  return JsonResponse({'error': 'Forbidden'}, status=403)

              # Set client context for RLS
              set_client_context(user.client_id)

              return func(request, *args, **kwargs)
          return wrapper
      return decorator

  @require_permission('view_findings')
  def get_findings(request):
      # Query automatically filtered by RLS
      findings = Finding.objects.filter(severity='Critical')
      return JsonResponse({'findings': list(findings)})
```

---

### 4. GroupMQ Integration Architecture

**Repository**: https://github.com/Openpanel-dev/groupmq.git

```yaml
GroupMQ Deployment:
  Host: iac1 (100.100.101.1)
  Port: 6379 (Redis-compatible)
  Protocol: TCP
  Persistence: Enabled (RDB + AOF)
  Clustering: Single node (initially), can scale horizontally

Topic/Queue Structure:

1. Scan Job Distribution:
   Topics:
     - scans/queued/{client_id}      # New scan requests
     - scans/assigned/{worker_id}    # Scan assigned to worker
     - scans/progress/{scan_id}      # Scan progress updates
     - scans/completed/{client_id}   # Scan finished
     - scans/failed/{scan_id}        # Scan errors

   Message Flow:
     Client requests scan
       ↓
     API publishes to scans/queued/client_acme
       {
         "scan_id": "scan_123",
         "client_id": "client_acme",
         "scan_type": "trivy",
         "target": "docker.io/nginx:latest",
         "priority": "high",  # Enterprise clients = high
         "created_at": "2025-10-11T22:00:00Z"
       }
       ↓
     Scanner Worker (subscribed to scans/queued/*) picks up job
       ↓
     Worker publishes to scans/assigned/worker_1
       ↓
     Worker runs scan and publishes progress to scans/progress/scan_123
       {
         "scan_id": "scan_123",
         "progress": 45,  # percentage
         "status": "scanning",
         "findings_count": 12
       }
       ↓
     Worker completes and publishes to scans/completed/client_acme
       {
         "scan_id": "scan_123",
         "status": "completed",
         "findings_count": 25,
         "critical": 2,
         "high": 8,
         "medium": 12,
         "low": 3
       }

2. Real-Time Notifications:
   Topics:
     - alerts/{client_id}/critical   # Critical finding alerts
     - alerts/{client_id}/high       # High severity alerts
     - alerts/{client_id}/medium     # Medium severity alerts
     - notifications/{client_id}/email   # Email notifications queue
     - notifications/{client_id}/webhook # Webhook deliveries
     - notifications/{client_id}/sms     # SMS alerts (optional)

   WebSocket Server:
     - Subscribes to alerts/{client_id}/*
     - Maintains WebSocket connections per client
     - Pushes real-time alerts to browser

   Example:
     New critical finding detected
       ↓
     Publish to alerts/client_acme/critical
       {
         "finding_id": 456,
         "title": "SQL Injection in login.php",
         "severity": "Critical",
         "cvss": 9.8,
         "url": "https://portal.insa-automation.com/findings/456"
       }
       ↓
     Multiple subscribers:
       - WebSocket server → Browser notification
       - Email service → Send email
       - Webhook service → POST to client's webhook URL
       - Audit service → Log the alert

3. AI Triage Queue:
   Topics:
     - triage/pending/{client_id}    # Findings awaiting triage
     - triage/in_progress/{worker_id} # AI worker processing
     - triage/completed/{client_id}  # Triage decisions
     - triage/learning/{client_id}   # Learning data for retraining

   Message Flow:
     100 findings imported from Trivy scan
       ↓
     API publishes 100 messages to triage/pending/client_acme
       ↓
     AI Worker pool (3 workers) subscribe to triage/pending/*
       ↓
     Each worker picks up findings and publishes to triage/in_progress/worker_ai_1
       ↓
     AI analyzes (EPSS + Claude Code + learning data)
       ↓
     Worker publishes to triage/completed/client_acme
       {
         "finding_id": 789,
         "triage_decision": "valid",
         "confidence": 0.92,
         "reasoning": "High EPSS score (0.85), active exploit available, affects production",
         "priority": "urgent",
         "sla_hours": 24
       }
       ↓
     Learning service subscribes to triage/completed/* and updates model

4. Client Onboarding Workflow:
   Topics:
     - onboarding/new_client           # New signup
     - onboarding/create_wazuh_product # Step 1
     - onboarding/create_dd_product    # Step 2
     - onboarding/generate_api_keys    # Step 3
     - onboarding/send_welcome_email   # Step 4
     - onboarding/complete             # Final step

   Orchestrator subscribes to all topics and coordinates workflow

5. Audit Event Stream:
   Topics:
     - audit/api_calls/*               # All API activity
     - audit/logins/*                  # Login events
     - audit/data_access/*             # Data view/edit events
     - audit/admin_actions/*           # Privileged operations

   Audit Service subscribes to audit/* and writes to append-only log

6. Billing & Usage Tracking:
   Topics:
     - billing/usage/{client_id}       # Usage events
     - billing/overages/{client_id}    # Over quota alerts
     - billing/invoices/generated      # New invoice created

Configuration:
  # groupmq.conf
  bind 0.0.0.0
  port 6379
  requirepass <strong_password>
  maxmemory 4gb
  maxmemory-policy allkeys-lru

  # Topic persistence
  save 900 1       # Save if 1 key changed in 900 seconds
  save 300 10      # Save if 10 keys changed in 300 seconds
  save 60 10000    # Save if 10,000 keys changed in 60 seconds

  # AOF (Append-Only File) for durability
  appendonly yes
  appendfsync everysec

Monitoring:
  - Queue depth per topic (alert if > 10,000)
  - Message publish rate (messages/sec)
  - Message consume rate (messages/sec)
  - Consumer lag (time since last message processed)
  - Dead letter queue depth (failed message retries)

GroupMQ vs Alternatives:
  ✅ GroupMQ: Lightweight, Redis-compatible, easy to deploy
  ⚠️ RabbitMQ: More mature, more complex setup
  ⚠️ Apache Kafka: Overkill for initial scale, heavyweight
  ⚠️ AWS SQS: Vendor lock-in, additional costs
```

---

### 5. Scanner Pool Architecture

```yaml
Scanner Workers:
  Deployment: Docker containers on iac1
  Count: 3-5 workers initially (auto-scale based on queue depth)
  Resources per worker:
    CPU: 2 cores
    Memory: 4GB
    Disk: 20GB

Scanners Integrated:
  1. Trivy (container/image scanning):
     - Scans Docker images
     - Detects vulnerabilities in OS packages
     - Detects vulnerabilities in application dependencies
     - SBOM generation
     - Policy enforcement

  2. OWASP ZAP (web application scanning):
     - Active scanning
     - Passive scanning
     - Spider (crawl website)
     - AJAX spider
     - Authentication support
     - API scanning

  3. Nmap (network discovery):
     - Port scanning
     - Service detection
     - OS detection
     - Vulnerability scripts (NSE)

  4. Nikto (web server scanning):
     - Server misconfiguration detection
     - Outdated server detection
     - Dangerous files/CGI
     - Default files
     - SSL/TLS issues

  5. Custom scanners (extensible):
     - Client-specific tools
     - Industry-specific scanners
     - Compliance checkers

Worker Implementation (Python example):
  import groupmq
  import trivy
  import requests
  import json

  # Connect to GroupMQ
  mq = groupmq.connect('localhost:6379', password='***')

  # Subscribe to scan queue
  @mq.subscribe('scans/queued/*')
  def handle_scan_request(message):
      scan_data = json.loads(message.body)
      scan_id = scan_data['scan_id']
      client_id = scan_data['client_id']
      scan_type = scan_data['scan_type']
      target = scan_data['target']

      # Publish to assigned queue
      mq.publish(f'scans/assigned/{worker_id}', {
          'scan_id': scan_id,
          'worker_id': worker_id
      })

      # Run scan
      if scan_type == 'trivy':
          results = trivy.scan_image(target)
      elif scan_type == 'zap':
          results = zap.scan_url(target)

      # Import results to DefectDojo
      api_key = get_client_api_key(client_id)
      defectdojo_product_id = get_defectdojo_product_id(client_id)

      response = requests.post(
          'http://localhost:8082/api/v2/import-scan/',
          headers={'Authorization': f'Token {api_key}'},
          files={'file': results},
          data={
              'scan_type': scan_type,
              'product_id': defectdojo_product_id,
              'engagement_id': engagement_id,
              'active': True,
              'verified': False
          }
      )

      # Publish completion
      mq.publish(f'scans/completed/{client_id}', {
          'scan_id': scan_id,
          'status': 'completed',
          'findings_count': response.json()['statistics']['findings_count']
      })

      # Queue for AI triage
      for finding_id in response.json()['findings']:
          mq.publish(f'triage/pending/{client_id}', {
              'finding_id': finding_id,
              'client_id': client_id
          })

  # Start worker
  mq.run()

Auto-Scaling Logic:
  - Monitor scans/queued/* depth
  - If queue depth > 100 for 5 minutes:
      Launch new scanner worker (Docker container)
  - If queue depth < 10 for 30 minutes:
      Terminate idle workers (keep minimum 2)

Rate Limiting per Client:
  Basic Tier: Max 2 concurrent scans
  Pro Tier: Max 10 concurrent scans
  Enterprise Tier: Max 50 concurrent scans
```

---

### 6. White-Labeling Implementation

```yaml
Brand: Insa Automation Corp
Primary Color: #1a56db (Blue)
Secondary Color: #f59e0b (Amber)
Logo: INSA logo (to be provided)

Components to White-Label:

1. DefectDojo:
   Location: /opt/django-DefectDojo/

   Changes:
     A. Environment variables (.env.prod):
        DD_SITE_NAME="Insa SecureOps Platform"
        DD_TEAM_NAME="Insa Automation Corp"
        DD_DISCLAIMER="Powered by Insa Automation Corp. Confidential."
        DD_FOOTER_TEXT="© 2025 Insa Automation Corp. All rights reserved."
        DD_ENABLE_PRODUCT_TRACKING_FILES=True

     B. Logo replacement:
        Path: dojo/static/dojo/img/
        Files to replace:
          - chop.png → insa_logo.png
          - favicon.ico → insa_favicon.ico
          - login-logo.png → insa_login_logo.png

     C. Custom CSS:
        Path: dojo/static/dojo/css/
        File: custom.css
        Content:
          :root {
            --primary-color: #1a56db;
            --secondary-color: #f59e0b;
            --logo-url: url('/static/dojo/img/insa_logo.png');
          }

          .navbar-brand {
            content: var(--logo-url);
          }

          /* Override default DefectDojo colors */
          .btn-primary {
            background-color: var(--primary-color);
          }

     D. Email templates:
        Path: dojo/templates/notifications/
        Update all email templates with Insa branding

     E. Report templates:
        Path: dojo/templates/defectdojo-engagement-report.html
        Add Insa logo to report headers
        Update footer with Insa contact info

2. Client Portal (Custom React/Vue App):
   Repository: insa-client-portal (to be created)

   Features:
     - Login page with Insa branding
     - Dashboard showing:
       * Finding statistics
       * Recent scans
       * SLA status
       * Usage metrics
     - Findings table (searchable, filterable)
     - Scan scheduler
     - Report generator
     - User management (for client admins)
     - API key management
     - Billing & usage page

   Tech Stack:
     - Frontend: React + TypeScript + Tailwind CSS
     - State management: Redux Toolkit
     - API client: Axios
     - Charts: Chart.js or Recharts
     - Notifications: react-toastify
     - Real-time: WebSocket client for GroupMQ

   Branding:
     - Logo: Insa Automation Corp logo
     - Color scheme: Blue (#1a56db) + Amber (#f59e0b)
     - Font: Inter or Roboto
     - Icons: Heroicons or FontAwesome

3. API Documentation:
   Tool: Swagger/OpenAPI + Redoc
   URL: https://api.insa-automation.com/docs

   Branding:
     - Custom Redoc theme with Insa colors
     - Logo in header
     - Footer with Insa contact info

4. Status Page:
   Tool: Uptime Robot + custom status page
   URL: https://status.insa-automation.com

   Shows:
     - API status (operational, degraded, down)
     - Dashboard status
     - Scanner pool status
     - Incident history
     - Scheduled maintenance

5. Marketing Website:
   URL: https://www.insa-automation.com

   Pages:
     - Home (product overview)
     - Features
     - Pricing
     - Documentation
     - About Us
     - Contact
     - Legal (Terms, Privacy Policy, DPA)

6. Custom Domain Configuration:
   Domains to register:
     - insa-automation.com (main)
     - insasecureops.com (product-specific)

   DNS Records:
     - A: @                  → iac1 public IP
     - A: portal             → iac1 public IP
     - A: api                → iac1 public IP
     - A: status             → Status page IP
     - CNAME: www            → insa-automation.com
     - MX:                   → Email provider
     - TXT: _dmarc           → DMARC policy
     - TXT: @                → SPF record

   SSL Certificates:
     - Tool: Let's Encrypt (automatic via Traefik)
     - Wildcard cert: *.insa-automation.com
```

---

### 7. Client Onboarding Automation

```yaml
Automated Onboarding Workflow:

Step 1: Client Signup (Web Form)
  URL: https://portal.insa-automation.com/signup

  Form Fields:
    - Company Name
    - Contact Name
    - Email
    - Phone (optional)
    - Number of assets to monitor (for pricing)
    - Industry (for compliance)
    - Preferred plan (Basic, Pro, Enterprise)
    - Payment info (credit card)

  On Submit:
    - Validate inputs
    - Check email doesn't exist
    - Generate unique client_id: "client_<company_slug>"
    - Hash password
    - Insert into clients table
    - Publish to GroupMQ: onboarding/new_client

Step 2: Create Wazuh Product (if applicable for tier)
  Subscriber: Onboarding service

  Actions:
    - Call Wazuh Manager API to create new Product
    - Store Wazuh product_id
    - Publish to: onboarding/create_wazuh_product_done

Step 3: Create DefectDojo Product
  Actions:
    - Call DefectDojo API:
      POST /api/v2/products/
      {
        "name": "ACME Corp Security",
        "description": "Security findings for ACME Corp",
        "prod_type": 1,
        "tags": ["client_acme"]
      }
    - Store DefectDojo product_id
    - Insert into defectdojo_products table
    - Publish to: onboarding/create_dd_product_done

Step 4: Generate API Keys
  Actions:
    - Generate API key: dd_api_key_acme_<random>
    - Hash and store in clients table
    - Generate initial user account for client admin
    - Create user in users table
    - Send API key via secure method (encrypted email or portal)
    - Publish to: onboarding/generate_api_keys_done

Step 5: Provision Initial Resources
  Actions:
    - Create AI learning database for client: /var/lib/defectdojo/learning_client_acme.db
    - Create file storage directory: /var/lib/defectdojo/clients/client_acme/
    - Set up default scan policies
    - Create default webhook endpoints (if provided)
    - Publish to: onboarding/provision_resources_done

Step 6: Send Welcome Email
  Actions:
    - Compose email with:
      * Welcome message
      * Login credentials (temporary password)
      * API key (secure link to retrieve)
      * Quick start guide link
      * Agent deployment instructions
      * Support contact info
    - Send via email service (SendGrid, Mailgun, etc.)
    - Publish to: onboarding/send_welcome_email_done

Step 7: Run Initial Baseline Scan (Optional)
  Actions:
    - If client provided initial target during signup
    - Queue baseline scan to GroupMQ: scans/queued/client_acme
    - Scan completes → AI triage → Email initial report
    - Publish to: onboarding/baseline_scan_done

Step 8: Mark Onboarding Complete
  Actions:
    - Update clients table: onboarding_status = 'complete'
    - Log to audit trail
    - Notify INSA sales team (internal notification)
    - Start billing cycle
    - Publish to: onboarding/complete

Total Time: < 5 minutes (automated)

Onboarding Orchestrator Implementation:
  import groupmq
  import defectdojo_api
  import wazuh_api
  import email_service
  import db

  mq = groupmq.connect('localhost:6379')

  @mq.subscribe('onboarding/new_client')
  def start_onboarding(message):
      client_data = json.loads(message.body)
      client_id = client_data['client_id']

      try:
          # Step 2: Wazuh Product
          if client_data['tier'] in ['pro', 'enterprise']:
              wazuh_product_id = wazuh_api.create_product(
                  name=client_data['company_name']
              )
              db.save_wazuh_product(client_id, wazuh_product_id)
          mq.publish('onboarding/create_wazuh_product_done', {'client_id': client_id})

          # Step 3: DefectDojo Product
          dd_product_id = defectdojo_api.create_product(
              name=f"{client_data['company_name']} Security"
          )
          db.save_dd_product(client_id, dd_product_id)
          mq.publish('onboarding/create_dd_product_done', {'client_id': client_id})

          # Step 4: API Keys
          api_key = generate_api_key(client_id)
          db.save_api_key(client_id, api_key)
          mq.publish('onboarding/generate_api_keys_done', {'client_id': client_id, 'api_key': api_key})

          # Step 5: Provision Resources
          provision_storage(client_id)
          provision_ai_db(client_id)
          mq.publish('onboarding/provision_resources_done', {'client_id': client_id})

          # Step 6: Welcome Email
          email_service.send_welcome_email(
              to=client_data['email'],
              api_key=api_key,
              login_url='https://portal.insa-automation.com/login'
          )
          mq.publish('onboarding/send_welcome_email_done', {'client_id': client_id})

          # Step 7: Baseline Scan (if target provided)
          if client_data.get('initial_target'):
              mq.publish('scans/queued/' + client_id, {
                  'scan_type': 'nmap',
                  'target': client_data['initial_target'],
                  'priority': 'normal'
              })

          # Step 8: Complete
          db.update_client_status(client_id, 'active', 'onboarding_complete')
          mq.publish('onboarding/complete', {'client_id': client_id})

          # Notify INSA team
          email_service.send_internal_notification(
              subject=f"New Client Onboarded: {client_data['company_name']}",
              body=f"Client ID: {client_id}\nTier: {client_data['tier']}\nEmail: {client_data['email']}"
          )

      except Exception as e:
          # Publish to dead letter queue
          mq.publish('onboarding/failed', {
              'client_id': client_id,
              'error': str(e)
          })
          # Alert INSA team
          email_service.send_alert('Onboarding failed for ' + client_id)

Manual Onboarding Fallback:
  If automated onboarding fails:
    1. Alert sent to support@insa-automation.com
    2. Support team manually provisions client
    3. Root cause analysis to fix automation
    4. Update onboarding orchestrator
```

---

## Next Document

This architecture document will be followed by:

1. ✅ Complete: netg security stack audit
2. ✅ Complete: Internal vs SaaS comparison
3. ✅ **IN PROGRESS**: Multi-tenant architecture design
4. **NEXT**: White-label DefectDojo implementation guide
5. **THEN**: Client onboarding automation code
6. **THEN**: SOC 2/ISO 27001 compliance roadmap

---

**Document**: MULTI_TENANT_SAAS_SOC_ARCHITECTURE.md
**Status**: Design Complete
**Next Steps**: Begin white-labeling DefectDojo on iac1
**Date**: 2025-10-11
**Author**: Claude Code

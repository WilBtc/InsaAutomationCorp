# Internal Security vs SaaS Security Comparison
**Date**: 2025-10-11
**Purpose**: Define requirements for transforming INSA's internal SOC into a multi-tenant SaaS offering
**Brand**: Insa Automation Corp

---

## Executive Summary

This document outlines the **critical differences** between operating an internal Security Operations Center (SOC) and offering **Security-as-a-Service (SecaaS)** to external clients. Understanding these differences is essential for successfully launching "**Insa Automation Corp SecureOps Platform**".

**Key Insight**: Your netg internal SOC is excellent - but SaaS requires **10x stricter isolation, compliance, and automation**.

---

## High-Level Comparison

| Dimension | Internal SOC (netg) | SaaS SOC (iac1 Target) |
|-----------|---------------------|------------------------|
| **Trust Model** | Trusted internal users | Zero-trust external clients |
| **Data Isolation** | Single organization | **MANDATORY** client separation |
| **Access Control** | LDAP/AD for employees | Per-client RBAC + API keys |
| **Compliance** | Internal policies | SOC 2, ISO 27001, GDPR, HIPAA |
| **Scalability** | Fixed # of assets | Must scale to hundreds of clients |
| **Availability** | Best effort | **99.9% SLA** with penalties |
| **Support** | Internal IT team | 24/7 customer support |
| **Monitoring** | Monitor others | **Must monitor yourself** too |
| **Branding** | Internal INSA | **White-labeled** "Insa Automation Corp" |
| **Billing** | Cost center | **Revenue generator** with metering |

---

## Detailed Requirements Matrix

### 1. Architecture & Infrastructure

#### Internal SOC (netg)

```yaml
Architecture:
  Type: Monolithic
  Tenancy: Single-tenant (INSA only)
  Servers:
    - netg: Central Wazuh Manager
    - iac1: Monitored agent
    - LU1: Monitored agent
    - ERP: Monitored agent (disconnected)

  Resources:
    CPU: Dedicated hardware
    Memory: Shared across all services
    Storage: Single filesystem

  Scaling:
    Strategy: Vertical (bigger server)
    Trigger: Performance degradation
    Automation: Manual

  Backup:
    Frequency: Daily (assumed)
    Retention: Local backups
    DR: No formal plan
```

#### SaaS SOC (Required)

```yaml
Architecture:
  Type: Multi-tenant microservices
  Tenancy: Strictly isolated per client
  Servers:
    - iac1: SaaS platform host
    - Optional: Per-client dedicated instances (Enterprise tier)

  Resources:
    CPU: Resource quotas per client
    Memory: Isolated memory limits per client
    Storage: Encrypted per-client databases

  Scaling:
    Strategy: Horizontal (add more servers)
    Trigger: Automated based on load
    Automation: Kubernetes/Docker Swarm autoscaling

  Backup:
    Frequency: Continuous (WAL archiving)
    Retention: 90 days minimum (compliance)
    DR: Multi-region with RTO < 4 hours

  Message Queue:
    System: GroupMQ (https://github.com/Openpanel-dev/groupmq.git)
    Purpose:
      - Distribute scan jobs across workers
      - Client notifications
      - Async task processing
      - Event streaming per client
    Features:
      - Per-client topics/queues
      - Rate limiting per client
      - Priority queues (Enterprise clients first)
      - Dead letter queues for failed jobs
```

---

### 2. Data Isolation & Security

#### Internal SOC (netg)

```yaml
Data Model:
  - Single Wazuh Manager database
  - All agents in one pool
  - Shared OpenVAS targets
  - No data encryption at rest
  - No per-user data access logs

Access Control:
  - Shared admin credentials
  - No audit trail per user
  - Trust-based access

Compliance:
  - Internal policies only
  - No third-party audits
```

#### SaaS SOC (Required)

```yaml
Data Model:
  Strategy: "Product per Client" in DefectDojo/Wazuh

  Client A:
    - Wazuh Product ID: client_a_prod_001
    - Database: defectdojo.products WHERE id=1
    - API Key: dd_api_key_clienta_*****
    - Encryption: AES-256 at rest
    - Findings: Only visible to Client A users
    - Agents: Only Client A servers

  Client B:
    - Wazuh Product ID: client_b_prod_002
    - Database: defectdojo.products WHERE id=2
    - API Key: dd_api_key_clientb_*****
    - Encryption: AES-256 at rest (different key)
    - Findings: Only visible to Client B users
    - Agents: Only Client B servers

  CRITICAL RULES:
    ❌ Client A MUST NEVER see Client B data
    ❌ API key of Client A MUST NEVER access Client B data
    ❌ Cross-client queries MUST be blocked at database level
    ✅ All data encrypted at rest (different keys per client)
    ✅ All API calls logged with client ID
    ✅ All database queries filtered by client_id
    ✅ All file uploads segregated by client directory

Access Control:
  - Per-client user accounts
  - Role-Based Access Control (RBAC):
    * Client Admin: Full access to their data
    * Client User: Read-only access to their data
    * Client API: Programmatic access to their data only
  - Multi-Factor Authentication (MFA) mandatory for admins
  - API key rotation every 90 days
  - IP whitelisting per client (optional)
  - Session timeout: 30 minutes

Audit Logging:
  - Every API call logged:
    * Timestamp
    * Client ID
    * User ID
    * Action performed
    * Data accessed
    * Source IP
    * Success/failure
  - Logs retained for 7 years (SOC 2 requirement)
  - Logs tamper-proof (append-only)
  - Real-time alerting on suspicious access patterns

Compliance:
  Required Certifications:
    - SOC 2 Type II (mandatory for enterprise clients)
    - ISO 27001 (optional but recommended)
    - GDPR compliance (if EU clients)
    - HIPAA compliance (if healthcare clients)
    - PCI-DSS (if handling payment card data)

  Data Residency:
    - Client data stored in client's preferred region
    - Cross-border data transfer restrictions
    - Data export on client request (GDPR right)
    - Data deletion within 30 days of termination (GDPR)
```

---

### 3. Multi-Tenancy Implementation

#### Database-Level Isolation

**Option A: Shared Database with Row-Level Security (RLS)** ⭐ Recommended

```sql
-- PostgreSQL Row-Level Security Example

-- Enable RLS on findings table
ALTER TABLE defectdojo_findings ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see findings from their client
CREATE POLICY client_isolation_policy ON defectdojo_findings
  FOR ALL
  TO PUBLIC
  USING (product_id IN (
    SELECT id FROM defectdojo_products
    WHERE client_id = current_setting('app.current_client_id')::int
  ));

-- Before each query, set client context
SET app.current_client_id = '42';  -- Client A

-- Now all queries are automatically filtered
SELECT * FROM defectdojo_findings;  -- Only returns Client A findings
```

**Benefits**:
- ✅ Single database to manage
- ✅ Cost-effective
- ✅ Easy backups
- ✅ Cross-client analytics possible (for INSA internal only)

**Challenges**:
- ⚠️ Must implement RLS perfectly (security risk if broken)
- ⚠️ Some enterprise clients may require dedicated DB
- ⚠️ Performance impact with millions of records

**Option B: Separate Database per Client** 🔒 Maximum Isolation

```yaml
Client A: postgresql://localhost:5432/insa_client_a
Client B: postgresql://localhost:5432/insa_client_b
Client C: postgresql://localhost:5432/insa_client_c
```

**Benefits**:
- ✅ Complete isolation (impossible to leak data)
- ✅ Easier compliance (physically separate)
- ✅ Per-client backups and restore
- ✅ Can sell as "dedicated database" premium feature

**Challenges**:
- ⚠️ Higher infrastructure costs
- ⚠️ More complex backup/restore
- ⚠️ Schema migrations across all databases

**Recommendation**: Start with Option A (RLS), offer Option B for Enterprise tier

---

#### Application-Level Isolation

```yaml
Every API Endpoint Must:
  1. Authenticate request (API key or JWT)
  2. Extract client_id from authentication
  3. Validate user has access to requested resource
  4. Filter all database queries by client_id
  5. Log the access attempt
  6. Return only client's data

Example API Call:
  Request:
    GET /api/v2/findings/
    Authorization: Token dd_api_key_clienta_abc123

  Backend Processing:
    1. Validate API key → Extract client_id = 'client_a'
    2. Query: SELECT * FROM findings WHERE product_id IN (
         SELECT id FROM products WHERE client_id = 'client_a'
       )
    3. Return JSON (only Client A findings)
    4. Log: "2025-10-11 21:45:32 | client_a | GET /findings/ | 200 OK | IP: 203.0.113.42"

Rate Limiting Per Client:
  Basic Tier:
    - 100 API calls / hour
    - 10 scans / day

  Pro Tier:
    - 1000 API calls / hour
    - 50 scans / day

  Enterprise Tier:
    - Unlimited API calls
    - Unlimited scans
    - Dedicated resources
```

---

#### File Storage Isolation

```yaml
Internal SOC (netg):
  - Shared /var/lib/defectdojo/
  - No access control on files

SaaS SOC (Required):
  Structure:
    /var/lib/defectdojo/
      clients/
        client_a/
          scans/
            2025-10-11-nessus-scan.xml (encrypted)
          reports/
            2025-10-weekly-report.pdf (encrypted)
          uploads/
            custom-wordlist.txt (encrypted)
        client_b/
          scans/
          reports/
          uploads/
        client_c/
          scans/
          reports/
          uploads/

  Encryption:
    - Each file encrypted with client-specific key
    - Keys stored in HashiCorp Vault or AWS KMS
    - File access logged in audit trail

  Permissions:
    - Application user: Read/write to specific client dirs
    - No direct shell access to client files
    - Automatic cleanup after 90 days (configurable)
```

---

### 4. Authentication & Authorization

#### Internal SOC (netg)

```yaml
Users:
  - Small team (< 10 people)
  - Everyone has admin access
  - Shared credentials common
  - No MFA required

Authentication:
  - Username/password
  - SSH keys for servers
  - Trust-based
```

#### SaaS SOC (Required)

```yaml
User Types:
  1. INSA Staff:
     - Super admins (full platform access)
     - Support staff (read-only across all clients)
     - Engineers (infrastructure management)

  2. Client Admins:
     - Full access to their organization's data
     - User management for their org
     - API key generation
     - Billing management

  3. Client Users:
     - Read-only or limited write access
     - Defined by Client Admin
     - MFA optional (recommended)

  4. Client API Keys:
     - Programmatic access
     - Scoped permissions
     - Rate limited
     - Rotatable

Authentication Methods:
  - Username/Password + MFA (mandatory for admins)
  - API Keys (for automation)
  - SSO/SAML (Enterprise tier):
    * Okta
    * Azure AD
    * Google Workspace
  - OAuth 2.0 (for integrations)

Authorization (RBAC):
  Roles:
    - platform_admin: INSA staff only
    - client_owner: Can do anything within their org
    - client_admin: Manage users, view/edit findings
    - client_analyst: View/triage findings, no admin
    - client_readonly: View findings only
    - client_api: API access with custom permissions

  Permissions:
    - view_findings
    - create_findings
    - triage_findings
    - close_findings
    - manage_products
    - manage_users
    - manage_integrations
    - generate_reports
    - view_billing
    - manage_billing

Session Management:
  - Session timeout: 30 minutes inactive
  - Concurrent session limit: 3 per user
  - Force logout on password change
  - IP-based anomaly detection
  - Alert on login from new location
```

---

### 5. API Design & Rate Limiting

#### Internal SOC (netg)

```yaml
API:
  - Wazuh Manager API on port 55000
  - No rate limiting
  - No versioning
  - Direct database access for admins
```

#### SaaS SOC (Required)

```yaml
API Architecture:
  Base URL: https://api.insa-automation.com/v2/

  Versioning:
    - v1: Legacy (deprecated)
    - v2: Current (stable)
    - v3: Beta (new features)

  Endpoints:
    # Authentication
    POST /auth/login
    POST /auth/logout
    POST /auth/refresh

    # Findings
    GET    /findings/                    # List findings
    GET    /findings/{id}/               # Get specific finding
    POST   /findings/                    # Create finding (import)
    PATCH  /findings/{id}/               # Update finding (triage)
    DELETE /findings/{id}/               # Delete finding

    # Products (client isolation unit)
    GET    /products/                    # List client's products
    GET    /products/{id}/               # Get specific product
    POST   /products/                    # Create product

    # Scans
    POST   /scans/import/                # Import scan results
    GET    /scans/                       # List scans
    GET    /scans/{id}/                  # Get scan details

    # Reports
    GET    /reports/                     # List available reports
    POST   /reports/generate/            # Generate new report
    GET    /reports/{id}/download/       # Download report PDF

    # Users (client admin only)
    GET    /users/                       # List org users
    POST   /users/                       # Create user
    PATCH  /users/{id}/                  # Update user
    DELETE /users/{id}/                  # Delete user

    # API Keys (client admin only)
    GET    /api-keys/                    # List org API keys
    POST   /api-keys/                    # Generate new API key
    DELETE /api-keys/{id}/               # Revoke API key

    # Webhooks
    GET    /webhooks/                    # List webhooks
    POST   /webhooks/                    # Create webhook
    DELETE /webhooks/{id}/               # Delete webhook

    # Metrics (usage stats)
    GET    /metrics/usage/               # Get usage stats
    GET    /metrics/findings-trend/      # Findings over time
    GET    /metrics/sla-status/          # SLA compliance

Rate Limiting:
  Strategy: Token bucket per client

  Basic Tier:
    - 100 requests / hour
    - Burst: 20 requests / minute
    - 429 Too Many Requests if exceeded

  Pro Tier:
    - 1000 requests / hour
    - Burst: 100 requests / minute

  Enterprise Tier:
    - 10,000 requests / hour
    - Burst: 500 requests / minute
    - Custom limits negotiable

  Implementation:
    - GroupMQ for distributed rate limiting
    - Redis for rate limit counters
    - Response headers:
      X-RateLimit-Limit: 1000
      X-RateLimit-Remaining: 847
      X-RateLimit-Reset: 1697043200

Error Handling:
  Standard HTTP Status Codes:
    - 200 OK: Success
    - 201 Created: Resource created
    - 400 Bad Request: Invalid input
    - 401 Unauthorized: Missing/invalid auth
    - 403 Forbidden: Insufficient permissions
    - 404 Not Found: Resource doesn't exist
    - 429 Too Many Requests: Rate limit exceeded
    - 500 Internal Server Error: Our fault
    - 503 Service Unavailable: Maintenance mode

  Error Response Format:
    {
      "error": "rate_limit_exceeded",
      "message": "API rate limit exceeded. Limit: 100/hour. Retry after: 2025-10-11T22:00:00Z",
      "retry_after": 3600,
      "docs_url": "https://docs.insa-automation.com/api/rate-limits"
    }

API Documentation:
  - OpenAPI 3.0 specification
  - Interactive docs: https://api.insa-automation.com/docs
  - Code examples in Python, JavaScript, Bash, PowerShell
  - Postman collection provided
  - Client SDKs (Python, JavaScript)
```

---

### 6. Monitoring & Observability

#### Internal SOC (netg)

```yaml
Monitoring:
  - Wazuh monitors agents
  - No monitoring of Wazuh itself
  - Manual checks for service health
  - No SLA tracking
```

#### SaaS SOC (Required)

```yaml
Self-Monitoring (Critical):
  "You must monitor your own SOC platform!"

  Infrastructure Monitoring:
    Tool: Prometheus + Grafana
    Metrics:
      - CPU usage per client
      - Memory usage per client
      - Disk I/O per client
      - Network traffic per client
      - API response time per endpoint
      - Database query performance
      - Queue depth (GroupMQ)
      - Cache hit rate (Redis)

    Alerts:
      - CPU > 80% for 5 minutes
      - Memory > 90%
      - Disk > 85%
      - API response time > 2 seconds
      - Database connections exhausted
      - Queue depth > 1000 messages

  Application Monitoring:
    Tool: APM (Prometheus + Grafana or Datadog)
    Metrics:
      - Request rate per client
      - Error rate per client
      - Response time (p50, p95, p99)
      - Database query time
      - Background job success rate
      - Scan completion rate
      - AI triage accuracy

    Distributed Tracing:
      - Trace ID in all logs
      - Request path visualization
      - Bottleneck identification

  Security Monitoring:
    Tool: Wazuh monitoring iac1 (reverse direction!)
    Events:
      - Failed login attempts
      - Suspicious API activity
      - Privilege escalation attempts
      - Data exfiltration patterns
      - DDoS attempts
      - SQL injection attempts

    SIEM Integration:
      - All security events to Wazuh on netg
      - Correlation rules for attacks
      - Automatic IP blocking (Fail2ban)
      - Alert SOC team on incidents

  SLA Tracking:
    Availability:
      Target: 99.9% uptime (43 minutes/month downtime)
      Measurement: HTTP health checks every 60 seconds
      Page: https://status.insa-automation.com
      Penalty: 10% monthly fee per 0.1% below target

    Performance:
      API Response Time: < 500ms (p95)
      Dashboard Load Time: < 3 seconds
      Report Generation: < 2 minutes
      Scan Import: < 5 minutes for 10,000 findings

    Support:
      Response Time:
        - Critical (P0): < 1 hour
        - High (P1): < 4 hours
        - Medium (P2): < 24 hours
        - Low (P3): < 72 hours

  Client-Specific Dashboards:
    Each client sees:
      - Their API usage (calls, rate limits)
      - Their scan history
      - Their finding trends
      - Their SLA compliance
      - Their billing/usage forecast
```

---

### 7. Incident Response & Support

#### Internal SOC (netg)

```yaml
Incident Response:
  - Internal IT team handles issues
  - No formal SLA
  - Best effort response
  - No 24/7 coverage

Support:
  - Email/Slack to IT team
  - No ticketing system
  - No customer support training
```

#### SaaS SOC (Required)

```yaml
Incident Response:
  Categories:
    P0 - Critical:
      - Platform down (all clients affected)
      - Data breach
      - Security incident
      Response: < 1 hour, 24/7
      Team: On-call engineer + manager

    P1 - High:
      - Client-specific outage
      - API completely unavailable
      - Data loss for client
      Response: < 4 hours, business hours
      Team: Support engineer

    P2 - Medium:
      - Performance degradation
      - Feature not working
      - Integration broken
      Response: < 24 hours
      Team: Support tier 1

    P3 - Low:
      - UI bug
      - Documentation error
      - Feature request
      Response: < 72 hours
      Team: Support tier 1

  On-Call Rotation:
    - 24/7 coverage (unless your SLA allows downtime)
    - PagerDuty or similar alerting
    - Escalation path defined
    - Post-incident review (PIR) for P0/P1

  Communication:
    - Status page: https://status.insa-automation.com
    - Email notifications to affected clients
    - In-app notifications
    - Slack/Teams integration (Enterprise tier)

Customer Support:
  Channels:
    - Email: support@insa-automation.com
    - Portal: https://portal.insa-automation.com/support
    - Chat: In-app live chat (Pro/Enterprise tiers)
    - Phone: +1-xxx-xxx-xxxx (Enterprise tier only)

  Ticketing System:
    - Tool: Zendesk, Freshdesk, or similar
    - Ticket routing by tier and expertise
    - SLA tracking per ticket
    - Customer satisfaction surveys

  Knowledge Base:
    - Self-service documentation
    - FAQs
    - Video tutorials
    - API documentation
    - Troubleshooting guides

  Training:
    - Support team trained on:
      * Product features
      * Customer empathy
      * Incident triage
      * Escalation procedures
      * Security incident handling
```

---

### 8. Backup & Disaster Recovery

#### Internal SOC (netg)

```yaml
Backup:
  - Assumed daily backups
  - Local storage
  - No tested restore procedures
  - No DR plan

RTO/RPO:
  - Not defined
  - Best effort recovery
```

#### SaaS SOC (Required)

```yaml
Backup Strategy:
  Frequency:
    - Continuous WAL archiving (PostgreSQL)
    - Full backup: Daily
    - Incremental backup: Every 6 hours
    - Transaction log backup: Every 15 minutes

  Retention:
    - Daily backups: 30 days
    - Weekly backups: 90 days
    - Monthly backups: 7 years (compliance)

  Storage:
    - Primary: S3 (encrypted)
    - Secondary: Glacier (long-term)
    - Geographic: Multi-region (us-east, us-west, eu-west)

  Validation:
    - Daily automated restore test
    - Monthly full DR drill
    - Quarterly disaster recovery exercise

Disaster Recovery:
  Scenarios:
    1. Database corruption:
       RTO: < 2 hours
       RPO: < 15 minutes
       Procedure: Restore from latest backup + WAL replay

    2. Complete server failure:
       RTO: < 4 hours
       RPO: < 15 minutes
       Procedure: Spin up new server, restore from backup

    3. Data center outage:
       RTO: < 8 hours
       RPO: < 1 hour
       Procedure: Failover to secondary region

    4. Ransomware attack:
       RTO: < 24 hours
       RPO: < 1 hour
       Procedure: Restore from air-gapped backup

  DR Site:
    - Warm standby in different region
    - Automatic failover for database
    - Manual failover for application (initially)
    - DNS TTL: 60 seconds for fast cutover

Data Export (GDPR):
  - Client can request full data export
  - Format: JSON, CSV, PDF
  - Delivered within 72 hours
  - Encrypted download link
```

---

### 9. Billing & Usage Tracking

#### Internal SOC (netg)

```yaml
Billing:
  - Cost center (no revenue)
  - No usage tracking
  - Fixed budget
```

#### SaaS SOC (Required)

```yaml
Usage Metering:
  Track per client:
    - Number of assets monitored
    - Number of scans performed
    - API calls made
    - Storage used (GB)
    - Bandwidth used (GB)
    - User seats

  Implementation:
    - Database table: client_usage_metrics
    - Daily aggregation job
    - Real-time counters (Redis)
    - GroupMQ events for usage spikes

Pricing Models:
  Option 1: Tiered Pricing
    Basic:
      - $99/month
      - 10 assets
      - 5 scans/month
      - 100 API calls/hour
      - 1 user
      - Email support

    Pro:
      - $499/month
      - 100 assets
      - 50 scans/month
      - 1000 API calls/hour
      - 10 users
      - Chat support
      - Custom reports

    Enterprise:
      - Custom pricing
      - Unlimited assets
      - Unlimited scans
      - Unlimited API
      - Unlimited users
      - Phone support
      - Dedicated account manager
      - SSO/SAML
      - SLA guarantees

  Option 2: Usage-Based Pricing
    - $5/asset/month
    - $10/scan
    - $0.001/API call
    - $10/GB storage
    - $20/user seat

  Option 3: Hybrid
    - Base fee + overage charges
    - Example: $299/month for 50 assets, $5/asset above 50

Billing System:
  - Tool: Stripe or similar
  - Automatic monthly invoicing
  - Credit card on file
  - Usage dashboard for client
  - Overage warnings at 80%/90%/100%
  - Automatic upgrade prompts
  - Dunning management (failed payments)
  - Annual discount (save 20%)

Cost Allocation:
  Per Client:
    - Infrastructure costs (compute, storage, bandwidth)
    - Third-party tool licenses (if per-user)
    - Support costs (based on ticket volume)

  Profitability Analysis:
    - Revenue per client
    - Cost per client
    - Profit margin per client
    - LTV (Lifetime Value)
    - CAC (Customer Acquisition Cost)
    - LTV:CAC ratio target > 3:1
```

---

### 10. Deployment & Operations

#### Internal SOC (netg)

```yaml
Deployment:
  - Manual server provisioning
  - Ansible scripts (found on netg)
  - No CI/CD
  - Updates during business hours
```

#### SaaS SOC (Required)

```yaml
Infrastructure as Code:
  - Terraform for server provisioning
  - Ansible for configuration management
  - Version controlled in Git
  - Peer-reviewed changes

CI/CD Pipeline:
  Steps:
    1. Code commit to Git
    2. Automated tests run:
       - Unit tests
       - Integration tests
       - Security scans (SAST)
       - Dependency checks
    3. Build Docker images
    4. Push to container registry
    5. Deploy to staging
    6. Automated testing on staging
    7. Manual approval
    8. Deploy to production (blue-green)
    9. Smoke tests
    10. Monitor for errors

  Tools:
    - GitHub Actions or GitLab CI
    - Docker + Docker Compose
    - Kubernetes (optional for scale)

Zero-Downtime Deployments:
  Strategy: Blue-Green Deployment
    - Blue: Current production
    - Green: New version
    - Switch traffic from Blue → Green
    - Monitor for issues
    - If problems: Instant rollback to Blue
    - If successful: Retire Blue

  Database Migrations:
    - Backward compatible migrations
    - Run migration before code deploy
    - Test rollback procedure
    - Lock-free migrations (avoid downtime)

Maintenance Windows:
  - Avoid if possible (zero-downtime deploys)
  - If required: Announce 48 hours in advance
  - Schedule during low-traffic hours (2-4 AM client timezone)
  - Duration: < 2 hours
  - Status page updated in real-time
```

---

## Message Queue Integration: GroupMQ

**Repository**: https://github.com/Openpanel-dev/groupmq.git

### Use Cases for SaaS SOC

```yaml
1. Scan Job Distribution:
   Problem: Multiple clients request scans simultaneously
   Solution:
     - Client A requests Nessus scan → GroupMQ topic: scans/client_a
     - Client B requests OWASP ZAP scan → GroupMQ topic: scans/client_b
     - Worker pool (5 scanner VMs) subscribe to scans/* topics
     - Jobs distributed with priority (Enterprise > Pro > Basic)
     - Results published to results/client_a, results/client_b

   Benefits:
     - Fair resource allocation
     - No client monopolizes scanners
     - Auto-scaling based on queue depth

2. Real-Time Notifications:
   Problem: Clients want instant alerts for critical findings
   Solution:
     - New critical finding detected → Publish to alerts/client_a
     - Client subscribes via WebSocket to alerts/client_a
     - Instant notification in browser/mobile app
     - Also sends email via alerts/email topic
     - Also triggers webhook via alerts/webhooks topic

   Benefits:
     - Real-time updates
     - Multi-channel delivery
     - Reliable delivery (retries)

3. AI Triage Queue:
   Problem: Thousands of findings need AI triage
   Solution:
     - Findings imported → Publish to triage/pending
     - AI workers subscribe to triage/pending
     - Each finding triaged → Publish to triage/completed
     - Learning system subscribes to triage/completed

   Benefits:
     - Parallel AI processing
     - No blocking imports
     - Audit trail of all triage decisions

4. Client Onboarding:
   Problem: New client signup takes 30 minutes of manual work
   Solution:
     - New signup → Publish to onboarding/new_client
     - Workflow orchestrator subscribes:
       Step 1: Create Wazuh Product → Publish to onboarding/wazuh_done
       Step 2: Create DefectDojo Product → Publish to onboarding/dd_done
       Step 3: Generate API keys → Publish to onboarding/keys_done
       Step 4: Send welcome email → Publish to onboarding/email_done
       Step 5: Mark complete → Publish to onboarding/complete

   Benefits:
     - Automated onboarding
     - Traceable steps
     - Error recovery (retry failed steps)

5. Rate Limiting:
   Problem: Client exceeds API rate limit
   Solution:
     - All API requests tracked in GroupMQ
     - Counter service subscribes to api/requests
     - Maintains rate limit state per client
     - Rejects requests if limit exceeded

   Benefits:
     - Distributed rate limiting
     - Accurate across multiple API servers

6. Event Sourcing & Audit:
   Problem: Need complete audit trail for compliance
   Solution:
     - Every state change → Event to GroupMQ
     - Example: Finding triaged → {event: "finding_triaged", finding_id: 123, client_id: "A", user_id: 42, old_state: "new", new_state: "valid", timestamp: "..."}
     - Audit service subscribes to all/* topics
     - Stores in append-only audit log

   Benefits:
     - Complete audit trail
     - Time-travel debugging
     - Compliance evidence
```

### GroupMQ Architecture for SaaS

```yaml
Topics Structure:
  clients/{client_id}/scans/requested
  clients/{client_id}/scans/in_progress
  clients/{client_id}/scans/completed
  clients/{client_id}/findings/new
  clients/{client_id}/findings/triaged
  clients/{client_id}/alerts/critical
  clients/{client_id}/alerts/high
  clients/{client_id}/webhooks
  platform/onboarding/new_client
  platform/onboarding/completed
  platform/billing/usage_event
  platform/audit/*

Producers:
  - API Server (publishes API events, scan requests)
  - Scanner Workers (publishes scan progress, results)
  - AI Triage Engine (publishes triage decisions)
  - Onboarding Service (publishes workflow steps)
  - Billing Service (publishes usage events)

Consumers:
  - Scanner Workers (subscribes to scan requests)
  - AI Triage Workers (subscribes to findings)
  - Notification Service (subscribes to alerts, emails, webhooks)
  - Audit Service (subscribes to all events)
  - Analytics Service (subscribes to usage events)
  - Client WebSocket Server (subscribes to client-specific topics)

Message Format:
  {
    "event_id": "evt_abc123xyz",
    "event_type": "scan.requested",
    "client_id": "client_a",
    "timestamp": "2025-10-11T21:45:00Z",
    "data": {
      "scan_type": "nessus",
      "target": "192.168.1.0/24",
      "scan_policy": "full",
      "priority": "high"
    },
    "metadata": {
      "user_id": "user_42",
      "api_key_id": "key_789",
      "source_ip": "203.0.113.42"
    }
  }

Retention:
  - Default: 7 days
  - Audit topics: 7 years
  - Billing topics: 10 years (tax records)

Monitoring:
  - Queue depth per topic
  - Message publish rate
  - Message consume rate
  - Consumer lag
  - Dead letter queue depth
  - Alert if queue depth > 10,000
```

---

## Summary: Critical SaaS Requirements

### Must-Have Before Launch

✅ **1. Multi-Tenancy with Perfect Data Isolation**
- Row-Level Security (RLS) in database
- Client ID in every query
- Separate file storage per client
- Audit logging of all data access

✅ **2. Authentication & Authorization**
- Per-client user accounts
- RBAC with fine-grained permissions
- API keys with rotation
- MFA for admins

✅ **3. White-Labeling**
- "Insa Automation Corp" branding everywhere
- Custom domain: portal.insa-automation.com
- Client-specific subdomains (optional)

✅ **4. Client Onboarding Automation**
- Self-service signup
- Automated provisioning (< 1 hour)
- Welcome email with credentials
- Initial scan and report

✅ **5. Monitoring & SLA Tracking**
- Self-monitoring of platform
- 99.9% uptime target
- Status page
- Alerting for downtime

✅ **6. Backup & DR**
- Continuous backups
- Tested restore procedures
- RTO < 4 hours, RPO < 15 minutes
- Multi-region redundancy

✅ **7. Billing & Usage Tracking**
- Metering per client
- Automated invoicing
- Overage alerts
- Payment gateway integration

✅ **8. Support Infrastructure**
- Ticketing system
- Knowledge base
- Email/chat support
- On-call rotation

✅ **9. API with Rate Limiting**
- RESTful API
- Per-client rate limits
- Comprehensive documentation
- Client SDKs

✅ **10. Compliance Documentation**
- SOC 2 Type II roadmap
- Privacy policy
- Terms of service
- Data processing agreements (GDPR)

---

## Next Steps

1. ✅ Complete: netg security stack audit
2. ✅ Complete: Internal vs SaaS comparison
3. **Next**: Multi-Tenant SaaS SOC Architecture Design
4. **Then**: White-Label DefectDojo POC
5. **Then**: Client Onboarding Automation
6. **Then**: SOC 2 / ISO 27001 Compliance Roadmap

---

**Document**: INTERNAL_VS_SAAS_SECURITY_COMPARISON.md
**Next**: MULTI_TENANT_SAAS_SOC_ARCHITECTURE.md
**Date**: 2025-10-11
**Author**: Claude Code

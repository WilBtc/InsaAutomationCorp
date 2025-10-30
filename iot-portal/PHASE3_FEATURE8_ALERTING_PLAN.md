# Phase 3 Feature 8: Advanced Alerting - Implementation Plan

**Feature**: Advanced Alerting with Escalation Policies
**Version**: 1.0
**Created**: October 28, 2025 04:00 UTC
**Status**: 🚀 READY TO IMPLEMENT
**Estimated Duration**: 2-3 weeks
**Priority**: HIGH (complements ML predictive maintenance)

---

## Executive Summary

Implement a comprehensive **Advanced Alerting System** with intelligent escalation, on-call rotation, alert grouping, and SLA tracking to transform the INSA Advanced IIoT Platform into a **24/7 operational excellence platform**.

**Business Value**:
- 70%+ reduction in alert fatigue (grouping & deduplication)
- 24/7 incident coverage (on-call rotation)
- Faster incident response (automated escalation)
- SLA compliance tracking (TTA/TTR metrics)
- Seamless ML integration (critical anomalies auto-escalate)

**Technical Scope**:
- Alert state machine (4 states: new, acknowledged, investigating, resolved)
- Escalation policy engine (configurable chains)
- On-call schedule management (weekly/daily rotation)
- Alert grouping & deduplication (reduce noise by 70%+)
- SLA tracking (time to acknowledge, time to resolve)
- 12 new API endpoints
- ML integration (auto-escalation for critical anomalies)
- Grafana alerting dashboard

---

## Current State Analysis

### Existing Alert System (Phase 2)

**Current Capabilities**:
- Basic alert creation via rule engine
- Email notifications (SMTP)
- Webhook notifications (8 security features)
- PostgreSQL storage (alerts table)

**Limitations**:
- No alert lifecycle management (alerts never acknowledged/resolved)
- No escalation (all alerts treated equally)
- No on-call rotation (manual assignment)
- No SLA tracking
- No alert grouping (100 identical alerts = 100 notifications)
- No integration with ML anomaly detection

**Database Schema** (existing):
```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id),
    rule_id UUID REFERENCES rules(id),
    severity VARCHAR(20) DEFAULT 'medium',
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
```

**Gaps to Address**:
1. ❌ No alert state tracking
2. ❌ No escalation mechanism
3. ❌ No on-call management
4. ❌ No SLA tracking
5. ❌ No alert grouping
6. ❌ No ML integration

---

## Target Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│             Advanced Alerting System                        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Alert State  │    │ Escalation   │    │  On-Call     │
│   Machine    │    │   Engine     │    │  Manager     │
│              │    │              │    │              │
│ 4 States     │    │ Policy-based │    │ Rotation     │
│ Transitions  │    │ Multi-tier   │    │ Schedule     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│Alert Grouping│   │SLA Tracking  │   │Notification  │
│Deduplication │   │TTA/TTR Metrics│  │Channels      │
└──────────────┘   └──────────────┘   └──────────────┘
                                              │
        ┌─────────────────────────────────────┼─────────────┐
        │                                     │             │
        ▼                                     ▼             ▼
┌──────────────┐                      ┌──────────┐  ┌──────────┐
│    Email     │                      │   SMS    │  │ Webhook  │
│    (SMTP)    │                      │ (Twilio) │  │ (Slack)  │
└──────────────┘                      └──────────┘  └──────────┘
```

### Component Overview

**1. Alert State Machine**
- Manages alert lifecycle (new → acknowledged → investigating → resolved)
- Tracks state transitions with timestamps
- Associates users with state changes
- Stores notes/comments per state

**2. Escalation Policy Engine**
- Evaluates escalation rules every 1 minute
- Executes multi-tier escalation chains
- Respects escalation delays (e.g., 5 min → 15 min → 30 min)
- Supports severity-based policies

**3. On-Call Schedule Manager**
- Manages weekly/daily rotation schedules
- Determines current on-call person
- Handles timezone conversions
- Supports vacation/holiday overrides

**4. Alert Grouping & Deduplication**
- Groups identical alerts (same device, same rule, same message)
- Deduplicates alerts within time window (e.g., 5 minutes)
- Reduces notification noise by 70%+

**5. SLA Tracking**
- Time to Acknowledge (TTA): Time from creation to acknowledged
- Time to Resolve (TTR): Time from creation to resolved
- Breach detection and notifications
- SLA compliance reporting

**6. Notification Channels**
- Email (existing SMTP)
- SMS (Twilio integration)
- Webhook (existing system + new targets like Slack, PagerDuty)
- In-app (WebSocket for real-time UI updates)

---

## Database Schema Design

### New Tables (4)

#### 1. alert_states

Tracks alert lifecycle and state transitions.

```sql
CREATE TABLE alert_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    state VARCHAR(50) NOT NULL,
    -- States: new, acknowledged, investigating, resolved
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    metadata JSONB DEFAULT '{}',

    -- Indexes
    INDEX idx_alert_states_alert_id (alert_id),
    INDEX idx_alert_states_state (state),
    INDEX idx_alert_states_changed_at (changed_at DESC)
);

-- Initial state trigger (auto-create 'new' state on alert creation)
CREATE OR REPLACE FUNCTION create_initial_alert_state()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO alert_states (alert_id, state, notes)
    VALUES (NEW.id, 'new', 'Alert created by system');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER alert_created_trigger
AFTER INSERT ON alerts
FOR EACH ROW
EXECUTE FUNCTION create_initial_alert_state();
```

**Purpose**: Track complete alert lifecycle with audit trail.

---

#### 2. escalation_policies

Stores escalation policy configurations.

```sql
CREATE TABLE escalation_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Escalation rules (JSONB array)
    rules JSONB NOT NULL,
    -- Example:
    -- [
    --   {"tier": 1, "delay_minutes": 0, "targets": ["user:uuid1", "oncall:schedule1"], "channels": ["email"]},
    --   {"tier": 2, "delay_minutes": 5, "targets": ["user:uuid2"], "channels": ["email", "sms"]},
    --   {"tier": 3, "delay_minutes": 15, "targets": ["oncall:schedule2"], "channels": ["sms", "webhook:slack"]}
    -- ]

    -- Severity filter (which severities this policy applies to)
    severities VARCHAR(20)[] DEFAULT ARRAY['critical', 'high', 'medium', 'low', 'info'],

    -- Status
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_escalation_policies_enabled (enabled),
    INDEX idx_escalation_policies_severities USING GIN (severities)
);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_escalation_policy_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER escalation_policy_updated_trigger
BEFORE UPDATE ON escalation_policies
FOR EACH ROW
EXECUTE FUNCTION update_escalation_policy_timestamp();
```

**Purpose**: Define escalation chains with multi-tier notification.

---

#### 3. on_call_schedules

Manages on-call rotation schedules.

```sql
CREATE TABLE on_call_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Schedule configuration (JSONB)
    schedule JSONB NOT NULL,
    -- Example (weekly rotation):
    -- {
    --   "type": "weekly",
    --   "rotation": [
    --     {"week": 1, "user_id": "uuid1", "start": "2025-10-28", "end": "2025-11-04"},
    --     {"week": 2, "user_id": "uuid2", "start": "2025-11-04", "end": "2025-11-11"}
    --   ],
    --   "overrides": [
    --     {"date": "2025-12-25", "user_id": "uuid3", "reason": "Holiday coverage"}
    --   ]
    -- }

    -- Example (daily rotation):
    -- {
    --   "type": "daily",
    --   "rotation": [
    --     {"day": "monday", "user_id": "uuid1"},
    --     {"day": "tuesday", "user_id": "uuid2"}
    --   ]
    -- }

    -- Timezone for schedule interpretation
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Status
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_on_call_schedules_enabled (enabled)
);
```

**Purpose**: Define on-call rotation schedules with overrides.

---

#### 4. alert_slas

Tracks SLA metrics for each alert.

```sql
CREATE TABLE alert_slas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL UNIQUE REFERENCES alerts(id) ON DELETE CASCADE,

    -- Severity determines SLA targets
    severity VARCHAR(20) NOT NULL,

    -- SLA Targets (minutes)
    tta_target INTEGER NOT NULL, -- Time to Acknowledge
    ttr_target INTEGER NOT NULL, -- Time to Resolve

    -- Actual times (NULL until event occurs)
    tta_actual INTEGER, -- Minutes from creation to acknowledged
    ttr_actual INTEGER, -- Minutes from creation to resolved

    -- Breach flags
    tta_breached BOOLEAN DEFAULT FALSE,
    ttr_breached BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,

    -- Indexes
    INDEX idx_alert_slas_alert_id (alert_id),
    INDEX idx_alert_slas_severity (severity),
    INDEX idx_alert_slas_tta_breached (tta_breached),
    INDEX idx_alert_slas_ttr_breached (ttr_breached)
);

-- Auto-create SLA on alert creation
CREATE OR REPLACE FUNCTION create_alert_sla()
RETURNS TRIGGER AS $$
DECLARE
    tta_mins INTEGER;
    ttr_mins INTEGER;
BEGIN
    -- Set SLA targets based on severity
    CASE NEW.severity
        WHEN 'critical' THEN
            tta_mins := 5;   -- 5 minutes to acknowledge
            ttr_mins := 30;  -- 30 minutes to resolve
        WHEN 'high' THEN
            tta_mins := 15;
            ttr_mins := 120;
        WHEN 'medium' THEN
            tta_mins := 60;
            ttr_mins := 480;
        WHEN 'low' THEN
            tta_mins := 240;
            ttr_mins := 1440;
        ELSE
            tta_mins := 1440;
            ttr_mins := 10080; -- 1 week
    END CASE;

    INSERT INTO alert_slas (alert_id, severity, tta_target, ttr_target)
    VALUES (NEW.id, NEW.severity, tta_mins, ttr_mins);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER alert_sla_created_trigger
AFTER INSERT ON alerts
FOR EACH ROW
EXECUTE FUNCTION create_alert_sla();
```

**Purpose**: Automatic SLA tracking with breach detection.

---

### Schema Modifications (Existing Tables)

#### alerts table (existing)

Add escalation tracking columns:

```sql
ALTER TABLE alerts
ADD COLUMN escalation_policy_id UUID REFERENCES escalation_policies(id),
ADD COLUMN current_escalation_tier INTEGER DEFAULT 0,
ADD COLUMN last_escalation_at TIMESTAMP,
ADD COLUMN grouped_alert_id UUID REFERENCES alerts(id), -- For grouped alerts
ADD COLUMN duplicate_count INTEGER DEFAULT 1; -- Count of deduplicated alerts

CREATE INDEX idx_alerts_escalation_policy ON alerts(escalation_policy_id);
CREATE INDEX idx_alerts_grouped_alert ON alerts(grouped_alert_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
```

**Purpose**: Track escalation state and alert grouping.

---

## API Endpoints Design

### Alert Management Endpoints (5)

#### 1. POST /api/v1/alerts/{id}/acknowledge

Acknowledge an alert (move to 'acknowledged' state).

**Request**:
```json
{
    "notes": "Investigating temperature spike on DEVICE-001"
}
```

**Response**:
```json
{
    "success": true,
    "alert_id": "uuid",
    "state": "acknowledged",
    "changed_by": "user@example.com",
    "changed_at": "2025-10-28T04:30:00Z",
    "tta_actual": 3, // minutes
    "sla_breached": false
}
```

**Business Logic**:
- Update alert state to 'acknowledged'
- Record user who acknowledged
- Update SLA metrics (tta_actual)
- Check for SLA breach
- Stop escalation for this alert

---

#### 2. POST /api/v1/alerts/{id}/investigate

Mark alert as being investigated.

**Request**:
```json
{
    "notes": "Root cause: cooling system failure"
}
```

**Response**:
```json
{
    "success": true,
    "alert_id": "uuid",
    "state": "investigating",
    "changed_by": "user@example.com",
    "changed_at": "2025-10-28T04:35:00Z"
}
```

**Business Logic**:
- Update alert state to 'investigating'
- Record user and timestamp
- Escalation still active (unlike acknowledged)

---

#### 3. POST /api/v1/alerts/{id}/resolve

Resolve an alert (final state).

**Request**:
```json
{
    "notes": "Cooling system repaired and tested",
    "resolution": "Replaced failed cooling fan motor"
}
```

**Response**:
```json
{
    "success": true,
    "alert_id": "uuid",
    "state": "resolved",
    "changed_by": "user@example.com",
    "changed_at": "2025-10-28T05:00:00Z",
    "ttr_actual": 30, // minutes
    "sla_breached": false,
    "resolution": "Replaced failed cooling fan motor"
}
```

**Business Logic**:
- Update alert state to 'resolved'
- Record resolution details
- Update SLA metrics (ttr_actual)
- Check for SLA breach
- Stop escalation permanently

---

#### 4. POST /api/v1/alerts/{id}/notes

Add notes/comments to an alert.

**Request**:
```json
{
    "notes": "Vendor contacted for replacement part",
    "internal": false
}
```

**Response**:
```json
{
    "success": true,
    "alert_id": "uuid",
    "note_id": "uuid",
    "created_by": "user@example.com",
    "created_at": "2025-10-28T04:45:00Z"
}
```

**Business Logic**:
- Add note to alert_states table
- Do not change alert state
- Support internal/external notes

---

#### 5. GET /api/v1/alerts/{id}/history

Get complete state history for an alert.

**Response**:
```json
{
    "success": true,
    "alert_id": "uuid",
    "current_state": "resolved",
    "history": [
        {
            "state": "new",
            "changed_by": "system",
            "changed_at": "2025-10-28T04:00:00Z",
            "notes": "Alert created by rule engine"
        },
        {
            "state": "acknowledged",
            "changed_by": "user@example.com",
            "changed_at": "2025-10-28T04:30:00Z",
            "notes": "Investigating temperature spike"
        },
        {
            "state": "investigating",
            "changed_by": "user@example.com",
            "changed_at": "2025-10-28T04:35:00Z",
            "notes": "Root cause: cooling system failure"
        },
        {
            "state": "resolved",
            "changed_by": "user@example.com",
            "changed_at": "2025-10-28T05:00:00Z",
            "notes": "Cooling system repaired",
            "resolution": "Replaced failed cooling fan motor"
        }
    ],
    "sla": {
        "tta_target": 5,
        "tta_actual": 30,
        "tta_breached": true,
        "ttr_target": 30,
        "ttr_actual": 60,
        "ttr_breached": true
    }
}
```

---

### Escalation Policy Endpoints (4)

#### 6. GET /api/v1/escalation-policies

List all escalation policies.

**Response**:
```json
{
    "success": true,
    "policies": [
        {
            "id": "uuid",
            "name": "Critical Alerts Policy",
            "description": "3-tier escalation for critical alerts",
            "rules": [...],
            "severities": ["critical"],
            "enabled": true
        }
    ],
    "total": 1
}
```

---

#### 7. POST /api/v1/escalation-policies

Create new escalation policy.

**Request**:
```json
{
    "name": "Critical Alerts Policy",
    "description": "3-tier escalation for critical alerts",
    "severities": ["critical"],
    "rules": [
        {
            "tier": 1,
            "delay_minutes": 0,
            "targets": ["oncall:primary"],
            "channels": ["email", "sms"]
        },
        {
            "tier": 2,
            "delay_minutes": 5,
            "targets": ["oncall:backup"],
            "channels": ["email", "sms", "webhook:slack"]
        },
        {
            "tier": 3,
            "delay_minutes": 15,
            "targets": ["user:manager-uuid"],
            "channels": ["email", "sms", "webhook:pagerduty"]
        }
    ]
}
```

**Response**:
```json
{
    "success": true,
    "policy_id": "uuid",
    "message": "Escalation policy created"
}
```

---

#### 8. PUT /api/v1/escalation-policies/{id}

Update escalation policy.

**Request**: Same as POST (full replacement)

**Response**:
```json
{
    "success": true,
    "policy_id": "uuid",
    "message": "Escalation policy updated"
}
```

---

#### 9. DELETE /api/v1/escalation-policies/{id}

Delete escalation policy.

**Response**:
```json
{
    "success": true,
    "message": "Escalation policy deleted"
}
```

**Business Logic**:
- Only delete if not in use by active alerts
- Return error if policy is referenced

---

### On-Call Management Endpoints (3)

#### 10. GET /api/v1/on-call/schedules

List all on-call schedules.

**Response**:
```json
{
    "success": true,
    "schedules": [
        {
            "id": "uuid",
            "name": "Primary On-Call",
            "type": "weekly",
            "timezone": "America/New_York",
            "enabled": true
        }
    ],
    "total": 1
}
```

---

#### 11. POST /api/v1/on-call/schedules

Create on-call schedule.

**Request**:
```json
{
    "name": "Primary On-Call",
    "description": "Weekly rotation for primary on-call",
    "timezone": "America/New_York",
    "schedule": {
        "type": "weekly",
        "rotation": [
            {"week": 1, "user_id": "uuid1", "start": "2025-10-28", "end": "2025-11-04"},
            {"week": 2, "user_id": "uuid2", "start": "2025-11-04", "end": "2025-11-11"}
        ]
    }
}
```

**Response**:
```json
{
    "success": true,
    "schedule_id": "uuid",
    "message": "On-call schedule created"
}
```

---

#### 12. GET /api/v1/on-call/current

Get current on-call person(s).

**Response**:
```json
{
    "success": true,
    "current_time": "2025-10-28T04:00:00Z",
    "on_call": [
        {
            "schedule_id": "uuid",
            "schedule_name": "Primary On-Call",
            "user_id": "uuid1",
            "user_name": "John Doe",
            "user_email": "john@example.com",
            "rotation_start": "2025-10-28T00:00:00Z",
            "rotation_end": "2025-11-04T00:00:00Z"
        }
    ]
}
```

**Business Logic**:
- Evaluate all enabled schedules
- Determine current on-call person per schedule
- Handle timezone conversions
- Respect overrides (holidays, vacations)

---

## Alert State Machine Design

### States (4)

```
┌─────────┐
│   new   │ ← Initial state (auto-created)
└────┬────┘
     │
     ▼
┌──────────────┐
│ acknowledged │ ← User acknowledges alert
└──────┬───────┘
       │
       ▼
┌──────────────┐
│investigating │ ← User is actively working on it
└──────┬───────┘
       │
       ▼
┌──────────┐
│ resolved │ ← Final state (alert closed)
└──────────┘
```

### Transitions

| From | To | Trigger | Who |
|------|----|----|-----|
| new | acknowledged | User acknowledges | Any authenticated user |
| new | investigating | User skips ack, starts investigating | Any authenticated user |
| new | resolved | Auto-resolve (e.g., condition cleared) | System |
| acknowledged | investigating | User starts investigation | Same or different user |
| acknowledged | resolved | Alert resolved without investigation | Same or different user |
| investigating | resolved | Investigation complete | Same or different user |
| resolved | new | Re-open (rare, for recurring issues) | Admin only |

### State Validation Rules

1. **new → acknowledged**: Always allowed
2. **new → investigating**: Always allowed (skip ack)
3. **acknowledged → investigating**: Always allowed
4. **acknowledged → resolved**: Always allowed (quick fix)
5. **investigating → resolved**: Always allowed
6. **resolved → new**: Admin only (re-open)
7. **Invalid transitions**: All other combinations rejected with error

---

## Escalation Policy Engine Design

### Escalation Flow

```
1. Alert Created (severity: critical)
   ↓
2. Assign Escalation Policy (based on severity)
   ↓
3. Start Escalation Timer
   ↓
4. Execute Tier 1 (delay: 0 min)
   - Notify: on-call primary via email + SMS
   ↓
5. Wait 5 minutes
   ↓
6. Check Alert State
   - If acknowledged → STOP escalation
   - If NOT acknowledged → Continue
   ↓
7. Execute Tier 2 (delay: 5 min)
   - Notify: on-call backup via email + SMS + Slack
   ↓
8. Wait 10 minutes
   ↓
9. Check Alert State
   - If acknowledged → STOP escalation
   - If NOT acknowledged → Continue
   ↓
10. Execute Tier 3 (delay: 15 min)
    - Notify: manager via email + SMS + PagerDuty
    ↓
11. Escalation Complete
    - Log final tier reached
    - Continue monitoring (alert remains active)
```

### Background Job: Escalation Monitor

**Frequency**: Every 1 minute

**Logic**:
```python
def escalation_monitor():
    # Get all unacknowledged alerts with escalation policies
    alerts = get_alerts(state=['new', 'investigating'],
                        has_policy=True)

    for alert in alerts:
        policy = get_escalation_policy(alert.escalation_policy_id)

        # Calculate time since alert creation
        time_elapsed = now() - alert.created_at

        # Find next tier to execute
        for tier in policy.rules:
            if time_elapsed >= tier.delay_minutes * 60:
                if alert.current_escalation_tier < tier.tier:
                    # Execute this tier
                    execute_escalation_tier(alert, tier)

                    # Update alert
                    alert.current_escalation_tier = tier.tier
                    alert.last_escalation_at = now()
                    save(alert)
```

### Escalation Execution

```python
def execute_escalation_tier(alert, tier):
    # Resolve targets (users, on-call schedules)
    recipients = resolve_targets(tier.targets)

    # Send notifications via each channel
    for channel in tier.channels:
        if channel == 'email':
            send_email(recipients, alert)
        elif channel == 'sms':
            send_sms(recipients, alert)
        elif channel.startswith('webhook:'):
            webhook_target = channel.split(':')[1]  # e.g., 'slack'
            send_webhook(webhook_target, alert)

    # Log escalation event
    log_escalation(alert.id, tier.tier, recipients, tier.channels)
```

---

## On-Call Schedule Manager Design

### Schedule Types

**1. Weekly Rotation**
- Users rotate every week
- Start day: Monday (configurable)
- Example: User A (week 1), User B (week 2), repeat

**2. Daily Rotation**
- Users assigned to specific days
- Example: User A (Mon/Wed/Fri), User B (Tue/Thu), User C (Sat/Sun)

**3. Custom Rotation**
- Users rotate at custom intervals (2 weeks, 1 month, etc.)

### Determining Current On-Call

```python
def get_current_on_call(schedule_id):
    schedule = get_schedule(schedule_id)

    # Get current time in schedule timezone
    now_tz = datetime.now(timezone(schedule.timezone))

    # Check for overrides first (holidays, vacations)
    override = find_override(schedule, now_tz.date())
    if override:
        return override.user_id

    # Determine rotation based on type
    if schedule.schedule['type'] == 'weekly':
        return determine_weekly_rotation(schedule, now_tz)
    elif schedule.schedule['type'] == 'daily':
        return determine_daily_rotation(schedule, now_tz)
    elif schedule.schedule['type'] == 'custom':
        return determine_custom_rotation(schedule, now_tz)
```

### Background Job: On-Call Rotation Update

**Frequency**: Every 1 hour

**Purpose**: Cache current on-call person for quick lookup

```python
def update_on_call_cache():
    schedules = get_enabled_schedules()

    for schedule in schedules:
        current_user = get_current_on_call(schedule.id)

        # Cache in Redis for fast lookup
        redis.set(f'oncall:{schedule.id}', current_user, ex=3600)
```

---

## Alert Grouping & Deduplication Design

### Grouping Strategy

**Group Key**: `{device_id}:{rule_id}:{severity}`

**Logic**:
```python
def create_alert(device_id, rule_id, severity, message):
    # Calculate group key
    group_key = f"{device_id}:{rule_id}:{severity}"

    # Check for existing alert in last 5 minutes
    existing_alert = find_recent_alert(
        group_key=group_key,
        time_window=timedelta(minutes=5),
        states=['new', 'acknowledged']
    )

    if existing_alert:
        # Group this alert with existing one
        existing_alert.duplicate_count += 1
        existing_alert.metadata['last_occurrence'] = now()
        save(existing_alert)

        # Create shadow alert (for audit)
        create_shadow_alert(
            grouped_alert_id=existing_alert.id,
            device_id=device_id,
            rule_id=rule_id,
            severity=severity,
            message=message
        )

        return existing_alert
    else:
        # Create new alert (no grouping)
        return create_new_alert(device_id, rule_id, severity, message)
```

### Deduplication Benefits

**Before Grouping**:
- 100 identical alerts → 100 notifications → Alert fatigue

**After Grouping**:
- 100 identical alerts → 1 notification → 70%+ noise reduction
- Grouped alert shows count: "Temperature high (×100)"

---

## SLA Tracking Design

### SLA Targets by Severity

| Severity | TTA Target | TTR Target |
|----------|------------|------------|
| critical | 5 min | 30 min |
| high | 15 min | 2 hours |
| medium | 1 hour | 8 hours |
| low | 4 hours | 24 hours |
| info | 24 hours | 1 week |

### SLA Calculation

**Time to Acknowledge (TTA)**:
```python
def calculate_tta(alert):
    if alert.acknowledged_at:
        tta_seconds = (alert.acknowledged_at - alert.created_at).total_seconds()
        tta_minutes = int(tta_seconds / 60)

        # Update SLA
        sla = get_alert_sla(alert.id)
        sla.tta_actual = tta_minutes
        sla.tta_breached = (tta_minutes > sla.tta_target)
        sla.acknowledged_at = alert.acknowledged_at
        save(sla)
```

**Time to Resolve (TTR)**:
```python
def calculate_ttr(alert):
    if alert.resolved_at:
        ttr_seconds = (alert.resolved_at - alert.created_at).total_seconds()
        ttr_minutes = int(ttr_seconds / 60)

        # Update SLA
        sla = get_alert_sla(alert.id)
        sla.ttr_actual = ttr_minutes
        sla.ttr_breached = (ttr_minutes > sla.ttr_target)
        sla.resolved_at = alert.resolved_at
        save(sla)
```

### SLA Breach Monitoring

**Background Job**: SLA Monitor (every 5 minutes)

```python
def monitor_sla_breaches():
    # Get all active alerts
    alerts = get_alerts(states=['new', 'acknowledged', 'investigating'])

    for alert in alerts:
        sla = get_alert_sla(alert.id)
        time_elapsed = (now() - alert.created_at).total_seconds() / 60

        # Check TTA breach (if not acknowledged yet)
        if not alert.acknowledged_at:
            if time_elapsed > sla.tta_target and not sla.tta_breached:
                sla.tta_breached = True
                save(sla)

                # Send SLA breach notification
                notify_sla_breach(alert, 'TTA')

        # Check TTR breach (if not resolved yet)
        if not alert.resolved_at:
            if time_elapsed > sla.ttr_target and not sla.ttr_breached:
                sla.ttr_breached = True
                save(sla)

                # Send SLA breach notification
                notify_sla_breach(alert, 'TTR')
```

---

## ML Integration Design

### ML Anomaly → Critical Alert

When ML model detects critical anomaly (confidence > 0.95):

```python
def handle_ml_anomaly(prediction):
    if prediction['is_anomaly'] and prediction['confidence'] > 0.95:
        # Create critical alert
        alert = create_alert(
            device_id=prediction['device_id'],
            rule_id=None,  # ML-generated, no rule
            severity='critical',
            message=f"ML detected critical anomaly: {prediction['metric_name']} = {prediction['value']}",
            metadata={
                'source': 'ml',
                'model_id': prediction['model_id'],
                'anomaly_score': prediction['score'],
                'confidence': prediction['confidence']
            }
        )

        # Assign escalation policy for critical alerts
        critical_policy = get_escalation_policy(severity='critical')
        alert.escalation_policy_id = critical_policy.id
        save(alert)

        # Escalation will start automatically (tier 1, delay 0 min)
```

### Alert Grouping for ML Anomalies

ML anomalies grouped by: `{device_id}:{metric_name}:critical`

Example:
- 10 consecutive ML anomalies on same device/metric → 1 alert (×10)

---

## Twilio SMS Integration (Optional)

### Configuration

```python
# Environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')  # Your Twilio number
```

### SMS Sending

```python
from twilio.rest import Client

def send_sms(phone_number, message):
    if not TWILIO_ACCOUNT_SID:
        logger.warning("Twilio not configured, skipping SMS")
        return

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        logger.info(f"SMS sent to {phone_number}, SID: {sms.sid}")
        return sms.sid
    except Exception as e:
        logger.error(f"SMS send failed: {e}")
        return None

def format_alert_sms(alert):
    """Format alert for SMS (160 char limit)"""
    return f"[{alert.severity.upper()}] {alert.message[:100]}"
```

### Cost Estimation

- **Twilio SMS**: $0.0075/message
- **Estimated Volume**: 100 messages/month
- **Monthly Cost**: $0.75

---

## Testing Strategy

### Unit Tests (20+ tests)

**Alert State Machine** (8 tests):
1. ✅ Test state transition: new → acknowledged
2. ✅ Test state transition: new → investigating
3. ✅ Test state transition: acknowledged → investigating
4. ✅ Test state transition: acknowledged → resolved
5. ✅ Test state transition: investigating → resolved
6. ✅ Test invalid transition: new → resolved (should fail)
7. ✅ Test state history recording
8. ✅ Test notes attachment

**Escalation Policy** (6 tests):
1. ✅ Test policy creation with valid rules
2. ✅ Test policy validation (invalid JSON)
3. ✅ Test tier execution order
4. ✅ Test escalation stop on acknowledgement
5. ✅ Test severity filtering
6. ✅ Test multi-tier escalation (3 tiers)

**On-Call Rotation** (4 tests):
1. ✅ Test weekly rotation calculation
2. ✅ Test daily rotation calculation
3. ✅ Test timezone conversion
4. ✅ Test override handling (vacation/holiday)

**Alert Grouping** (3 tests):
1. ✅ Test alert grouping (same device/rule)
2. ✅ Test deduplication within time window
3. ✅ Test group count increment

**SLA Tracking** (5 tests):
1. ✅ Test TTA calculation
2. ✅ Test TTR calculation
3. ✅ Test TTA breach detection
4. ✅ Test TTR breach detection
5. ✅ Test SLA targets per severity

### Integration Tests (10+ tests)

**End-to-End Workflows** (10 tests):
1. ✅ Test complete alert lifecycle (new → resolved)
2. ✅ Test escalation execution (3 tiers)
3. ✅ Test on-call schedule integration
4. ✅ Test ML anomaly → critical alert → escalation
5. ✅ Test alert grouping in production
6. ✅ Test SLA tracking for critical alert
7. ✅ Test email notification delivery
8. ✅ Test SMS notification delivery (if Twilio configured)
9. ✅ Test webhook notification delivery
10. ✅ Test API authentication and authorization

**Total Tests**: 30+ (20 unit + 10 integration)
**Target Coverage**: 80%+

---

## Implementation Timeline

### Week 1: Core Alert Management (Days 1-5)

**Day 1: Database Schema**
- Create 4 new tables (alert_states, escalation_policies, on_call_schedules, alert_slas)
- Create triggers (auto-create initial state, auto-create SLA)
- Modify alerts table (add escalation columns)
- Write database migration script

**Day 2: Alert State Machine**
- Implement state transition logic
- Add state validation
- Create alert_states CRUD operations
- Write 8 unit tests

**Day 3-4: Alert Management API**
- Implement 5 API endpoints (acknowledge, investigate, resolve, notes, history)
- Add JWT authentication
- Add permission checks (RBAC integration)
- Write 5 integration tests

**Day 5: SLA Tracking**
- Implement SLA calculation (TTA, TTR)
- Create SLA breach detection
- Add background job (SLA monitor)
- Write 5 unit tests

**Deliverable**: Basic alert lifecycle management working

---

### Week 2: Escalation & On-Call (Days 6-10)

**Day 6: Escalation Policy Engine**
- Implement escalation policy CRUD
- Create escalation execution logic
- Add background job (escalation monitor, every 1 min)
- Write 6 unit tests

**Day 7: On-Call Schedule Manager**
- Implement on-call schedule CRUD
- Create rotation calculation (weekly, daily, custom)
- Add timezone support
- Write 4 unit tests

**Day 8: Notification Channels**
- Integrate Twilio SMS (optional)
- Enhance webhook system (Slack, PagerDuty targets)
- Test email notifications
- Write 3 integration tests

**Day 9: Alert Grouping & Deduplication**
- Implement grouping logic
- Add deduplication time window (5 min)
- Update alert creation flow
- Write 3 unit tests

**Day 10: API Endpoints (Escalation & On-Call)**
- Implement 7 API endpoints (4 escalation + 3 on-call)
- Add Swagger documentation
- Write 5 integration tests

**Deliverable**: Complete escalation and on-call system working

---

### Week 3: Integration & Testing (Days 11-15)

**Day 11: ML Integration**
- Connect ML anomaly detection to alert creation
- Implement auto-escalation for critical ML anomalies
- Test end-to-end flow (ML → alert → escalation)
- Write 3 integration tests

**Day 12: Grafana Dashboard**
- Create alerting analytics dashboard (8 panels)
- Add SLA compliance chart
- Add escalation timeline visualization
- Create provisioning script

**Day 13: Testing & Bug Fixes**
- Run all 30+ tests
- Fix any failures
- Achieve 80%+ code coverage
- Load testing (100 alerts/min)

**Day 14: Documentation**
- Write feature implementation guide
- Create API documentation
- Write user guide (how to use advanced alerting)
- Create troubleshooting guide

**Day 15: Production Deployment**
- Deploy to production
- Create sample escalation policies
- Set up on-call schedules
- Monitor for 24 hours

**Deliverable**: Production-ready advanced alerting system

---

## Success Criteria

### Functional Requirements ✅

1. ✅ Alert state machine with 4 states (new, acknowledged, investigating, resolved)
2. ✅ Escalation policies with multi-tier support
3. ✅ On-call schedule management (weekly, daily, custom)
4. ✅ Alert grouping reducing noise by 70%+
5. ✅ SLA tracking (TTA/TTR) with breach detection
6. ✅ ML integration (critical anomalies auto-escalate)
7. ✅ 12 new API endpoints working
8. ✅ Notification channels (email, SMS, webhook)

### Performance Requirements ✅

1. ✅ Escalation check <100ms per alert
2. ✅ SLA calculation <50ms per alert
3. ✅ Background jobs complete in <10 seconds
4. ✅ API response time <200ms (all endpoints)
5. ✅ Support 1000+ alerts per minute

### Quality Requirements ✅

1. ✅ 80%+ test coverage
2. ✅ Zero notification delivery failures
3. ✅ Zero escalation policy bypass vulnerabilities
4. ✅ 100% SLA tracking accuracy
5. ✅ Documentation complete (implementation + user guide)

---

## Risk Assessment

### Technical Risks

**Medium Risk:**
1. **Twilio SMS Integration**
   - Risk: SMS delivery failures, cost overruns
   - Mitigation: Make optional, add rate limiting, monitor costs
   - Contingency: Email-only fallback

2. **Escalation Timing**
   - Risk: Background job delays causing missed escalations
   - Mitigation: 1-minute job frequency, monitoring alerts
   - Contingency: Increase job frequency to 30 seconds

**Low Risk:**
3. **Database Performance**
   - Risk: Many triggers/functions slowing inserts
   - Mitigation: Optimize queries, add indexes
   - Contingency: Async processing via queue

4. **Timezone Handling**
   - Risk: Incorrect on-call determination due to timezone bugs
   - Mitigation: Thorough testing, use pytz library
   - Contingency: Default to UTC, manual overrides

### Business Risks

**Low Risk:**
1. **Alert Fatigue** (solved by grouping)
2. **SLA Breach Notifications** (avoid notification loops)
3. **On-Call Burnout** (rotation ensures distribution)

---

## Dependencies

### External Libraries

```
# Add to requirements.txt
twilio>=8.0.0          # SMS notifications (optional)
pytz>=2023.3           # Timezone handling
```

### Internal Dependencies

**Required Features** (already complete):
- ✅ RBAC (Phase 3 Feature 5) - User management
- ✅ Email notifications (Phase 2 Feature 4)
- ✅ Webhook system (Phase 2 Feature 5)
- ✅ PostgreSQL database (Phase 2)
- ✅ JWT authentication (Phase 3 Feature 5)

**Integration Points**:
- ✅ ML anomaly detection (Phase 3 Feature 2)
- ✅ Rule engine (Phase 2 Feature 3)
- ✅ Grafana (Phase 2 Feature 7)

---

## Next Steps

### Immediate Tasks (This Session)

1. ✅ Create this implementation plan
2. 🔄 Create database schema file (`alerting_schema.sql`)
3. 🔄 Write unit tests for alert state machine
4. 🔄 Implement alert state machine module
5. 🔄 Create API endpoint stubs

### Short-Term (Week 1)

1. Complete database schema deployment
2. Implement all 5 alert management API endpoints
3. Add SLA tracking
4. Write and pass 13 tests (8 state machine + 5 API)

### Medium-Term (Week 2)

1. Implement escalation policy engine
2. Implement on-call schedule manager
3. Add Twilio SMS integration
4. Implement alert grouping
5. Write and pass 17 additional tests

### Long-Term (Week 3)

1. ML integration
2. Grafana dashboard
3. Complete testing (30+ tests)
4. Documentation
5. Production deployment

---

## Appendix: File Structure

```
/home/wil/iot-portal/
├── alerting_schema.sql               (NEW - database schema)
├── alert_state_machine.py            (NEW - state management)
├── escalation_engine.py              (NEW - escalation logic)
├── on_call_manager.py                (NEW - on-call rotation)
├── alert_grouping.py                 (NEW - grouping/dedup)
├── sla_tracker.py                    (NEW - SLA calculations)
├── alerting_api.py                   (NEW - 12 API endpoints)
├── notification_channels.py          (NEW - SMS, webhook)
├── test_alert_state_machine.py       (NEW - 8 unit tests)
├── test_escalation_engine.py         (NEW - 6 unit tests)
├── test_on_call_manager.py           (NEW - 4 unit tests)
├── test_alert_grouping.py            (NEW - 3 unit tests)
├── test_sla_tracker.py               (NEW - 5 unit tests)
├── test_alerting_integration.py      (NEW - 10 integration tests)
├── grafana_alerting_dashboard.json   (NEW - Grafana config)
├── provision_alerting_dashboard.py   (NEW - dashboard provisioner)
├── PHASE3_FEATURE8_ALERTING_PLAN.md  (THIS FILE)
└── PHASE3_FEATURE8_COMPLETE.md       (FUTURE - implementation docs)
```

**Total New Files**: 17
**Estimated Lines of Code**: ~3,500
**Estimated Documentation**: ~1,500 lines

---

**Status**: ✅ READY TO IMPLEMENT
**Created**: October 28, 2025 04:00 UTC
**Author**: INSA Automation Corp - Advanced Alerting Team
**Review**: Pending user approval

---

*This implementation plan provides complete architecture, design, and timeline for Feature 8 (Advanced Alerting). Ready to proceed with database schema creation and TDD implementation.*

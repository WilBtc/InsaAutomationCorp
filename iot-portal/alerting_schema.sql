-- Advanced Alerting System - Database Schema
-- INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8
-- Created: October 28, 2025 04:15 UTC
--
-- This schema adds advanced alerting capabilities:
-- 1. Alert state tracking (lifecycle management)
-- 2. Escalation policies (multi-tier notification)
-- 3. On-call schedules (rotation management)
-- 4. SLA tracking (TTA/TTR metrics)
--
-- Dependencies: PostgreSQL 14+, existing alerts table
-- Run: psql -h localhost -U iiot_user -d insa_iiot -f alerting_schema.sql

-- =============================================================================
-- TABLE 1: alert_states
-- Purpose: Track alert lifecycle with complete state history
-- =============================================================================

CREATE TABLE IF NOT EXISTS alert_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,

    -- State values: new, acknowledged, investigating, resolved
    state VARCHAR(50) NOT NULL CHECK (state IN ('new', 'acknowledged', 'investigating', 'resolved')),

    -- Audit trail
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Optional notes for this state transition
    notes TEXT,

    -- Additional metadata (JSON)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_state CHECK (state IN ('new', 'acknowledged', 'investigating', 'resolved'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_alert_states_alert_id ON alert_states(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_states_state ON alert_states(state);
CREATE INDEX IF NOT EXISTS idx_alert_states_changed_at ON alert_states(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_states_changed_by ON alert_states(changed_by);

-- Comments
COMMENT ON TABLE alert_states IS 'Alert lifecycle state tracking with complete audit trail';
COMMENT ON COLUMN alert_states.state IS 'Current state: new, acknowledged, investigating, resolved';
COMMENT ON COLUMN alert_states.changed_by IS 'User who triggered this state change (NULL for system)';
COMMENT ON COLUMN alert_states.notes IS 'Optional notes describing this state change';


-- =============================================================================
-- TABLE 2: escalation_policies
-- Purpose: Define multi-tier escalation chains for alerts
-- =============================================================================

CREATE TABLE IF NOT EXISTS escalation_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Escalation rules as JSONB array
    -- Example: [
    --   {"tier": 1, "delay_minutes": 0, "targets": ["oncall:primary"], "channels": ["email", "sms"]},
    --   {"tier": 2, "delay_minutes": 5, "targets": ["oncall:backup"], "channels": ["email", "sms", "webhook:slack"]},
    --   {"tier": 3, "delay_minutes": 15, "targets": ["user:manager-uuid"], "channels": ["sms", "webhook:pagerduty"]}
    -- ]
    rules JSONB NOT NULL,

    -- Severity filter (which alert severities this policy applies to)
    -- Array allows multiple severities: ['critical', 'high']
    severities VARCHAR(20)[] DEFAULT ARRAY['critical', 'high', 'medium', 'low', 'info'],

    -- Status
    enabled BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_severities CHECK (
        severities <@ ARRAY['critical', 'high', 'medium', 'low', 'info']::VARCHAR(20)[]
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_escalation_policies_enabled ON escalation_policies(enabled);
CREATE INDEX IF NOT EXISTS idx_escalation_policies_severities ON escalation_policies USING GIN (severities);
CREATE INDEX IF NOT EXISTS idx_escalation_policies_name ON escalation_policies(name);

-- Comments
COMMENT ON TABLE escalation_policies IS 'Multi-tier escalation policies for alert notifications';
COMMENT ON COLUMN escalation_policies.rules IS 'JSONB array of escalation tiers with targets and channels';
COMMENT ON COLUMN escalation_policies.severities IS 'Array of alert severities this policy applies to';


-- =============================================================================
-- TABLE 3: on_call_schedules
-- Purpose: Manage on-call rotation schedules with timezone support
-- =============================================================================

CREATE TABLE IF NOT EXISTS on_call_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Schedule configuration as JSONB
    -- Weekly rotation example:
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
    --
    -- Daily rotation example:
    -- {
    --   "type": "daily",
    --   "rotation": [
    --     {"day": "monday", "user_id": "uuid1"},
    --     {"day": "tuesday", "user_id": "uuid2"}
    --   ]
    -- }
    schedule JSONB NOT NULL,

    -- Timezone for schedule interpretation (IANA timezone string)
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Status
    enabled BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_schedule_type CHECK (
        schedule->>'type' IN ('weekly', 'daily', 'custom')
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_on_call_schedules_enabled ON on_call_schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_on_call_schedules_name ON on_call_schedules(name);

-- Comments
COMMENT ON TABLE on_call_schedules IS 'On-call rotation schedules with timezone support';
COMMENT ON COLUMN on_call_schedules.schedule IS 'JSONB configuration for rotation (weekly, daily, custom)';
COMMENT ON COLUMN on_call_schedules.timezone IS 'IANA timezone string (e.g., America/New_York)';


-- =============================================================================
-- TABLE 4: alert_slas
-- Purpose: Track SLA metrics (TTA/TTR) for each alert
-- =============================================================================

CREATE TABLE IF NOT EXISTS alert_slas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL UNIQUE REFERENCES alerts(id) ON DELETE CASCADE,

    -- Severity determines SLA targets
    severity VARCHAR(20) NOT NULL,

    -- SLA Targets (in minutes)
    tta_target INTEGER NOT NULL,  -- Time to Acknowledge
    ttr_target INTEGER NOT NULL,  -- Time to Resolve

    -- Actual times (NULL until event occurs)
    tta_actual INTEGER,  -- Actual time to acknowledge (minutes)
    ttr_actual INTEGER,  -- Actual time to resolve (minutes)

    -- Breach flags
    tta_breached BOOLEAN DEFAULT FALSE,
    ttr_breached BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_severity CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    CONSTRAINT valid_tta_target CHECK (tta_target > 0),
    CONSTRAINT valid_ttr_target CHECK (ttr_target > 0),
    CONSTRAINT valid_tta_actual CHECK (tta_actual IS NULL OR tta_actual >= 0),
    CONSTRAINT valid_ttr_actual CHECK (ttr_actual IS NULL OR ttr_actual >= 0)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_alert_slas_alert_id ON alert_slas(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_slas_severity ON alert_slas(severity);
CREATE INDEX IF NOT EXISTS idx_alert_slas_tta_breached ON alert_slas(tta_breached);
CREATE INDEX IF NOT EXISTS idx_alert_slas_ttr_breached ON alert_slas(ttr_breached);
CREATE INDEX IF NOT EXISTS idx_alert_slas_created_at ON alert_slas(created_at DESC);

-- Comments
COMMENT ON TABLE alert_slas IS 'SLA tracking for alerts (Time to Acknowledge, Time to Resolve)';
COMMENT ON COLUMN alert_slas.tta_target IS 'Target time to acknowledge (minutes) based on severity';
COMMENT ON COLUMN alert_slas.ttr_target IS 'Target time to resolve (minutes) based on severity';
COMMENT ON COLUMN alert_slas.tta_actual IS 'Actual time to acknowledge (minutes), NULL if not acked';
COMMENT ON COLUMN alert_slas.ttr_actual IS 'Actual time to resolve (minutes), NULL if not resolved';


-- =============================================================================
-- MODIFY EXISTING TABLE: alerts
-- Purpose: Add escalation tracking columns
-- =============================================================================

-- Add new columns for escalation tracking
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS escalation_policy_id UUID REFERENCES escalation_policies(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS current_escalation_tier INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_escalation_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS grouped_alert_id UUID REFERENCES alerts(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS duplicate_count INTEGER DEFAULT 1;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_alerts_escalation_policy ON alerts(escalation_policy_id);
CREATE INDEX IF NOT EXISTS idx_alerts_grouped_alert ON alerts(grouped_alert_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);

-- Add constraints
ALTER TABLE alerts
ADD CONSTRAINT IF NOT EXISTS valid_escalation_tier CHECK (current_escalation_tier >= 0),
ADD CONSTRAINT IF NOT EXISTS valid_duplicate_count CHECK (duplicate_count >= 1);

-- Comments
COMMENT ON COLUMN alerts.escalation_policy_id IS 'Reference to escalation policy for this alert';
COMMENT ON COLUMN alerts.current_escalation_tier IS 'Current tier in escalation chain (0 = not escalated yet)';
COMMENT ON COLUMN alerts.last_escalation_at IS 'Timestamp of last escalation tier execution';
COMMENT ON COLUMN alerts.grouped_alert_id IS 'Reference to parent alert if this is a grouped/duplicate alert';
COMMENT ON COLUMN alerts.duplicate_count IS 'Count of deduplicated alerts grouped into this one';


-- =============================================================================
-- TRIGGER 1: Auto-create initial alert state
-- Purpose: Automatically create 'new' state when alert is created
-- =============================================================================

CREATE OR REPLACE FUNCTION create_initial_alert_state()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO alert_states (alert_id, state, notes, changed_by)
    VALUES (NEW.id, 'new', 'Alert created by system', NULL);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists, then create
DROP TRIGGER IF EXISTS alert_created_trigger ON alerts;

CREATE TRIGGER alert_created_trigger
AFTER INSERT ON alerts
FOR EACH ROW
EXECUTE FUNCTION create_initial_alert_state();

COMMENT ON FUNCTION create_initial_alert_state IS 'Auto-create initial state (new) for new alerts';


-- =============================================================================
-- TRIGGER 2: Auto-create SLA tracking
-- Purpose: Automatically create SLA record with targets based on severity
-- =============================================================================

CREATE OR REPLACE FUNCTION create_alert_sla()
RETURNS TRIGGER AS $$
DECLARE
    tta_mins INTEGER;
    ttr_mins INTEGER;
BEGIN
    -- Set SLA targets based on severity
    CASE NEW.severity
        WHEN 'critical' THEN
            tta_mins := 5;      -- 5 minutes to acknowledge
            ttr_mins := 30;     -- 30 minutes to resolve
        WHEN 'high' THEN
            tta_mins := 15;     -- 15 minutes
            ttr_mins := 120;    -- 2 hours
        WHEN 'medium' THEN
            tta_mins := 60;     -- 1 hour
            ttr_mins := 480;    -- 8 hours
        WHEN 'low' THEN
            tta_mins := 240;    -- 4 hours
            ttr_mins := 1440;   -- 24 hours
        ELSE
            tta_mins := 1440;   -- 24 hours (info/unknown)
            ttr_mins := 10080;  -- 1 week
    END CASE;

    INSERT INTO alert_slas (alert_id, severity, tta_target, ttr_target)
    VALUES (NEW.id, NEW.severity, tta_mins, ttr_mins);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists, then create
DROP TRIGGER IF EXISTS alert_sla_created_trigger ON alerts;

CREATE TRIGGER alert_sla_created_trigger
AFTER INSERT ON alerts
FOR EACH ROW
EXECUTE FUNCTION create_alert_sla();

COMMENT ON FUNCTION create_alert_sla IS 'Auto-create SLA tracking with severity-based targets';


-- =============================================================================
-- TRIGGER 3: Update escalation policy timestamp
-- Purpose: Auto-update updated_at when escalation policy is modified
-- =============================================================================

CREATE OR REPLACE FUNCTION update_escalation_policy_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists, then create
DROP TRIGGER IF EXISTS escalation_policy_updated_trigger ON escalation_policies;

CREATE TRIGGER escalation_policy_updated_trigger
BEFORE UPDATE ON escalation_policies
FOR EACH ROW
EXECUTE FUNCTION update_escalation_policy_timestamp();

COMMENT ON FUNCTION update_escalation_policy_timestamp IS 'Auto-update updated_at timestamp on policy changes';


-- =============================================================================
-- TRIGGER 4: Update on-call schedule timestamp
-- Purpose: Auto-update updated_at when schedule is modified
-- =============================================================================

CREATE OR REPLACE FUNCTION update_on_call_schedule_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists, then create
DROP TRIGGER IF EXISTS on_call_schedule_updated_trigger ON on_call_schedules;

CREATE TRIGGER on_call_schedule_updated_trigger
BEFORE UPDATE ON on_call_schedules
FOR EACH ROW
EXECUTE FUNCTION update_on_call_schedule_timestamp();

COMMENT ON FUNCTION update_on_call_schedule_timestamp IS 'Auto-update updated_at timestamp on schedule changes';


-- =============================================================================
-- HELPER FUNCTION: Get current alert state
-- Purpose: Retrieve the most recent state for an alert
-- =============================================================================

CREATE OR REPLACE FUNCTION get_current_alert_state(p_alert_id UUID)
RETURNS VARCHAR(50) AS $$
DECLARE
    current_state VARCHAR(50);
BEGIN
    SELECT state INTO current_state
    FROM alert_states
    WHERE alert_id = p_alert_id
    ORDER BY changed_at DESC
    LIMIT 1;

    RETURN COALESCE(current_state, 'unknown');
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_current_alert_state IS 'Get most recent state for an alert';


-- =============================================================================
-- HELPER FUNCTION: Check if alert is acknowledged
-- Purpose: Quick check if alert has been acknowledged
-- =============================================================================

CREATE OR REPLACE FUNCTION is_alert_acknowledged(p_alert_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    ack_state BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM alert_states
        WHERE alert_id = p_alert_id
        AND state IN ('acknowledged', 'investigating', 'resolved')
    ) INTO ack_state;

    RETURN ack_state;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION is_alert_acknowledged IS 'Check if alert has been acknowledged (any non-new state)';


-- =============================================================================
-- VIEW: Current Alert States
-- Purpose: Simplified view of each alert's current state
-- =============================================================================

CREATE OR REPLACE VIEW v_current_alert_states AS
SELECT DISTINCT ON (a.id)
    a.id AS alert_id,
    a.device_id,
    a.severity,
    a.message,
    a.created_at,
    s.state AS current_state,
    s.changed_by,
    s.changed_at AS state_changed_at,
    s.notes,
    sla.tta_target,
    sla.tta_actual,
    sla.tta_breached,
    sla.ttr_target,
    sla.ttr_actual,
    sla.ttr_breached
FROM alerts a
LEFT JOIN alert_states s ON a.id = s.alert_id
LEFT JOIN alert_slas sla ON a.id = sla.alert_id
ORDER BY a.id, s.changed_at DESC;

COMMENT ON VIEW v_current_alert_states IS 'Current state and SLA status for all alerts';


-- =============================================================================
-- VIEW: Active Unacknowledged Alerts
-- Purpose: Alerts that need attention (for escalation monitoring)
-- =============================================================================

CREATE OR REPLACE VIEW v_active_unacknowledged_alerts AS
SELECT
    a.id AS alert_id,
    a.device_id,
    a.severity,
    a.message,
    a.created_at,
    a.escalation_policy_id,
    a.current_escalation_tier,
    a.last_escalation_at,
    EXTRACT(EPOCH FROM (NOW() - a.created_at)) / 60 AS age_minutes,
    sla.tta_target,
    sla.ttr_target
FROM alerts a
JOIN alert_slas sla ON a.id = sla.alert_id
WHERE get_current_alert_state(a.id) IN ('new', 'investigating')
AND a.escalation_policy_id IS NOT NULL
ORDER BY a.created_at ASC;

COMMENT ON VIEW v_active_unacknowledged_alerts IS 'Alerts requiring escalation (not acknowledged)';


-- =============================================================================
-- VIEW: SLA Compliance Summary
-- Purpose: Summary of SLA compliance metrics
-- =============================================================================

CREATE OR REPLACE VIEW v_sla_compliance_summary AS
SELECT
    severity,
    COUNT(*) AS total_alerts,
    COUNT(CASE WHEN tta_actual IS NOT NULL THEN 1 END) AS acknowledged_count,
    COUNT(CASE WHEN ttr_actual IS NOT NULL THEN 1 END) AS resolved_count,
    COUNT(CASE WHEN tta_breached THEN 1 END) AS tta_breaches,
    COUNT(CASE WHEN ttr_breached THEN 1 END) AS ttr_breaches,
    ROUND(AVG(tta_actual), 2) AS avg_tta_minutes,
    ROUND(AVG(ttr_actual), 2) AS avg_ttr_minutes,
    ROUND(100.0 * COUNT(CASE WHEN NOT tta_breached AND tta_actual IS NOT NULL THEN 1 END) /
          NULLIF(COUNT(CASE WHEN tta_actual IS NOT NULL THEN 1 END), 0), 2) AS tta_compliance_percent,
    ROUND(100.0 * COUNT(CASE WHEN NOT ttr_breached AND ttr_actual IS NOT NULL THEN 1 END) /
          NULLIF(COUNT(CASE WHEN ttr_actual IS NOT NULL THEN 1 END), 0), 2) AS ttr_compliance_percent
FROM alert_slas
GROUP BY severity
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        ELSE 5
    END;

COMMENT ON VIEW v_sla_compliance_summary IS 'SLA compliance metrics by severity';


-- =============================================================================
-- SAMPLE DATA: Default Escalation Policies
-- Purpose: Create example escalation policies for testing
-- =============================================================================

INSERT INTO escalation_policies (name, description, rules, severities)
VALUES
(
    'Critical Alerts - 3 Tier Escalation',
    'Aggressive escalation for critical alerts: immediate → 5min → 15min',
    '[
        {"tier": 1, "delay_minutes": 0, "targets": ["oncall:primary"], "channels": ["email", "sms"]},
        {"tier": 2, "delay_minutes": 5, "targets": ["oncall:backup"], "channels": ["email", "sms", "webhook:slack"]},
        {"tier": 3, "delay_minutes": 15, "targets": ["oncall:manager"], "channels": ["email", "sms", "webhook:pagerduty"]}
    ]'::jsonb,
    ARRAY['critical']
),
(
    'High Priority - 2 Tier Escalation',
    'Standard escalation for high priority alerts: immediate → 15min',
    '[
        {"tier": 1, "delay_minutes": 0, "targets": ["oncall:primary"], "channels": ["email"]},
        {"tier": 2, "delay_minutes": 15, "targets": ["oncall:backup"], "channels": ["email", "sms"]}
    ]'::jsonb,
    ARRAY['high']
),
(
    'Standard - Email Only',
    'Email-only notification for medium/low priority alerts',
    '[
        {"tier": 1, "delay_minutes": 0, "targets": ["oncall:primary"], "channels": ["email"]}
    ]'::jsonb,
    ARRAY['medium', 'low']
)
ON CONFLICT (name) DO NOTHING;


-- =============================================================================
-- SAMPLE DATA: Default On-Call Schedule
-- Purpose: Create example on-call schedule for testing
-- =============================================================================

-- Note: Replace user_id values with actual UUIDs from users table
INSERT INTO on_call_schedules (name, description, schedule, timezone)
VALUES
(
    'Primary Weekly Rotation',
    'Weekly on-call rotation (Monday start)',
    '{
        "type": "weekly",
        "rotation": [
            {"week": 1, "user_id": "00000000-0000-0000-0000-000000000001", "start": "2025-10-27", "end": "2025-11-03"},
            {"week": 2, "user_id": "00000000-0000-0000-0000-000000000002", "start": "2025-11-03", "end": "2025-11-10"}
        ],
        "overrides": []
    }'::jsonb,
    'America/New_York'
)
ON CONFLICT (name) DO NOTHING;


-- =============================================================================
-- GRANT PERMISSIONS
-- Purpose: Allow iiot_user to access all new tables and functions
-- =============================================================================

GRANT ALL PRIVILEGES ON TABLE alert_states TO iiot_user;
GRANT ALL PRIVILEGES ON TABLE escalation_policies TO iiot_user;
GRANT ALL PRIVILEGES ON TABLE on_call_schedules TO iiot_user;
GRANT ALL PRIVILEGES ON TABLE alert_slas TO iiot_user;

GRANT SELECT ON v_current_alert_states TO iiot_user;
GRANT SELECT ON v_active_unacknowledged_alerts TO iiot_user;
GRANT SELECT ON v_sla_compliance_summary TO iiot_user;

GRANT EXECUTE ON FUNCTION create_initial_alert_state() TO iiot_user;
GRANT EXECUTE ON FUNCTION create_alert_sla() TO iiot_user;
GRANT EXECUTE ON FUNCTION get_current_alert_state(UUID) TO iiot_user;
GRANT EXECUTE ON FUNCTION is_alert_acknowledged(UUID) TO iiot_user;


-- =============================================================================
-- VERIFICATION QUERIES
-- Purpose: Verify schema deployment
-- =============================================================================

-- Check tables created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('alert_states', 'escalation_policies', 'on_call_schedules', 'alert_slas')
ORDER BY table_name;

-- Check indexes created
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('alert_states', 'escalation_policies', 'on_call_schedules', 'alert_slas', 'alerts')
AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- Check triggers created
SELECT trigger_name, event_object_table, action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
AND event_object_table IN ('alerts', 'escalation_policies', 'on_call_schedules')
ORDER BY event_object_table, trigger_name;

-- Check views created
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public'
AND table_name LIKE 'v_%'
ORDER BY table_name;

-- Check sample data
SELECT COUNT(*) AS escalation_policy_count FROM escalation_policies;
SELECT COUNT(*) AS on_call_schedule_count FROM on_call_schedules;

-- =============================================================================
-- DEPLOYMENT SUMMARY
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Advanced Alerting Schema Deployment Complete';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables Created: 4 (alert_states, escalation_policies, on_call_schedules, alert_slas)';
    RAISE NOTICE 'Indexes Created: 15+';
    RAISE NOTICE 'Triggers Created: 4 (auto-create state, auto-create SLA, auto-update timestamps)';
    RAISE NOTICE 'Views Created: 3 (current states, active alerts, SLA compliance)';
    RAISE NOTICE 'Functions Created: 6 (state management, timestamp updates)';
    RAISE NOTICE 'Sample Policies: 3 escalation policies';
    RAISE NOTICE 'Sample Schedules: 1 on-call schedule';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Verify deployment: SELECT * FROM v_sla_compliance_summary;';
    RAISE NOTICE '2. Update on-call schedule user IDs with real users';
    RAISE NOTICE '3. Run tests: python3 test_alert_state_machine.py';
    RAISE NOTICE '4. Implement API endpoints: python3 alerting_api.py';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Schema is ready for Advanced Alerting implementation';
    RAISE NOTICE '=================================================================';
END $$;

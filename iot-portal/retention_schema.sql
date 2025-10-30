-- Data Retention Policies - Database Schema
-- INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 7
-- Created: October 28, 2025 23:05 UTC
--
-- This schema implements data retention and archival policies:
-- 1. Retention policy management
-- 2. Automated data purging
-- 3. Data archival
-- 4. Compliance tracking
--
-- Dependencies: PostgreSQL 14+, existing telemetry, alerts, audit_logs tables
-- Run: PGPASSWORD=iiot_secure_2025 psql -h localhost -U iiot_user -d insa_iiot -f retention_schema.sql

-- =============================================================================
-- TABLE: retention_policies
-- Purpose: Define data retention rules for different data types
-- =============================================================================

CREATE TABLE IF NOT EXISTS retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Data type this policy applies to
    data_type VARCHAR(50) NOT NULL CHECK (
        data_type IN ('telemetry', 'alerts', 'audit_logs', 'ml_anomalies', 'ml_training_data', 'all')
    ),

    -- Retention period (in days)
    retention_days INTEGER NOT NULL CHECK (retention_days > 0),

    -- Archive before delete (true = archive to cold storage, false = delete immediately)
    archive_before_delete BOOLEAN DEFAULT TRUE,

    -- Archive storage location (S3, filesystem, etc.)
    archive_location VARCHAR(255),

    -- Compression settings for archive
    compression VARCHAR(20) DEFAULT 'gzip' CHECK (
        compression IN ('none', 'gzip', 'bz2', 'xz')
    ),

    -- Filter criteria (JSONB for flexible filtering)
    -- Example: {"severity": ["low", "info"], "device_type": "sensor"}
    filter_criteria JSONB DEFAULT '{}'::jsonb,

    -- Execution schedule (cron expression)
    -- Example: "0 2 * * *" (daily at 2 AM)
    schedule VARCHAR(50) DEFAULT '0 2 * * *',

    -- Status
    enabled BOOLEAN DEFAULT TRUE,

    -- Last execution tracking
    last_executed_at TIMESTAMP,
    last_execution_status VARCHAR(20) CHECK (
        last_execution_status IS NULL OR
        last_execution_status IN ('success', 'failed', 'partial')
    ),
    last_execution_details JSONB,

    -- Statistics
    total_records_deleted BIGINT DEFAULT 0,
    total_records_archived BIGINT DEFAULT 0,
    total_bytes_freed BIGINT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT valid_retention_days CHECK (retention_days BETWEEN 1 AND 3650),  -- Max 10 years
    CONSTRAINT valid_schedule CHECK (schedule ~ '^[0-9*/,-]+ [0-9*/,-]+ [0-9*/,-]+ [0-9*/,-]+ [0-9*/,-]+$')
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_retention_policies_data_type ON retention_policies(data_type);
CREATE INDEX IF NOT EXISTS idx_retention_policies_enabled ON retention_policies(enabled);
CREATE INDEX IF NOT EXISTS idx_retention_policies_schedule ON retention_policies(schedule);
CREATE INDEX IF NOT EXISTS idx_retention_policies_last_executed ON retention_policies(last_executed_at);

-- Comments
COMMENT ON TABLE retention_policies IS 'Data retention and archival policies';
COMMENT ON COLUMN retention_policies.data_type IS 'Type of data: telemetry, alerts, audit_logs, ml_anomalies, ml_training_data, all';
COMMENT ON COLUMN retention_policies.retention_days IS 'Number of days to retain data before archival/deletion';
COMMENT ON COLUMN retention_policies.archive_before_delete IS 'If true, archive data before deletion; if false, delete immediately';
COMMENT ON COLUMN retention_policies.filter_criteria IS 'JSONB filter for selective retention (e.g., only delete low-severity alerts)';
COMMENT ON COLUMN retention_policies.schedule IS 'Cron expression for execution schedule';


-- =============================================================================
-- TABLE: retention_executions
-- Purpose: Track execution history of retention policies
-- =============================================================================

CREATE TABLE IF NOT EXISTS retention_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES retention_policies(id) ON DELETE CASCADE,

    -- Execution details
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds INTEGER,

    -- Execution status
    status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (
        status IN ('running', 'success', 'failed', 'partial')
    ),

    -- Results
    records_scanned BIGINT DEFAULT 0,
    records_deleted BIGINT DEFAULT 0,
    records_archived BIGINT DEFAULT 0,
    bytes_freed BIGINT DEFAULT 0,

    -- Error tracking
    error_message TEXT,
    error_details JSONB,

    -- Execution metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_duration CHECK (duration_seconds IS NULL OR duration_seconds >= 0)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_retention_executions_policy_id ON retention_executions(policy_id);
CREATE INDEX IF NOT EXISTS idx_retention_executions_started_at ON retention_executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_retention_executions_status ON retention_executions(status);

-- Comments
COMMENT ON TABLE retention_executions IS 'Execution history for retention policies';
COMMENT ON COLUMN retention_executions.records_scanned IS 'Number of records evaluated';
COMMENT ON COLUMN retention_executions.records_deleted IS 'Number of records deleted';
COMMENT ON COLUMN retention_executions.records_archived IS 'Number of records archived';


-- =============================================================================
-- TABLE: archived_data_index
-- Purpose: Index of archived data for retrieval
-- =============================================================================

CREATE TABLE IF NOT EXISTS archived_data_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES retention_policies(id) ON DELETE CASCADE,
    execution_id UUID NOT NULL REFERENCES retention_executions(id) ON DELETE CASCADE,

    -- Archive details
    data_type VARCHAR(50) NOT NULL,
    archive_path VARCHAR(500) NOT NULL,  -- Path to archived file
    archive_format VARCHAR(20) DEFAULT 'jsonl',  -- jsonl, csv, parquet
    compression VARCHAR(20) DEFAULT 'gzip',

    -- Data range
    data_start_date TIMESTAMP,
    data_end_date TIMESTAMP,
    record_count BIGINT,
    file_size_bytes BIGINT,

    -- Checksum for integrity verification
    checksum VARCHAR(64),  -- SHA256 hash

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    archived_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_date_range CHECK (
        data_start_date IS NULL OR data_end_date IS NULL OR
        data_start_date <= data_end_date
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_archived_data_policy_id ON archived_data_index(policy_id);
CREATE INDEX IF NOT EXISTS idx_archived_data_execution_id ON archived_data_index(execution_id);
CREATE INDEX IF NOT EXISTS idx_archived_data_type ON archived_data_index(data_type);
CREATE INDEX IF NOT EXISTS idx_archived_data_date_range ON archived_data_index(data_start_date, data_end_date);
CREATE INDEX IF NOT EXISTS idx_archived_data_archived_at ON archived_data_index(archived_at DESC);

-- Comments
COMMENT ON TABLE archived_data_index IS 'Index of archived data files for retrieval';
COMMENT ON COLUMN archived_data_index.archive_path IS 'File system path or S3 URL to archived data';
COMMENT ON COLUMN archived_data_index.checksum IS 'SHA256 checksum for integrity verification';


-- =============================================================================
-- TRIGGER: Update retention_policies timestamp
-- Purpose: Auto-update updated_at when policy is modified
-- =============================================================================

CREATE OR REPLACE FUNCTION update_retention_policy_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS retention_policy_updated_trigger ON retention_policies;

CREATE TRIGGER retention_policy_updated_trigger
BEFORE UPDATE ON retention_policies
FOR EACH ROW
EXECUTE FUNCTION update_retention_policy_timestamp();

COMMENT ON FUNCTION update_retention_policy_timestamp IS 'Auto-update updated_at timestamp on policy changes';


-- =============================================================================
-- TRIGGER: Update execution duration
-- Purpose: Auto-calculate duration when execution completes
-- =============================================================================

CREATE OR REPLACE FUNCTION calculate_execution_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND OLD.completed_at IS NULL THEN
        NEW.duration_seconds = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at))::INTEGER;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS execution_duration_trigger ON retention_executions;

CREATE TRIGGER execution_duration_trigger
BEFORE UPDATE ON retention_executions
FOR EACH ROW
EXECUTE FUNCTION calculate_execution_duration();

COMMENT ON FUNCTION calculate_execution_duration IS 'Auto-calculate execution duration';


-- =============================================================================
-- FUNCTION: Get retention policy statistics
-- Purpose: Retrieve policy execution statistics
-- =============================================================================

CREATE OR REPLACE FUNCTION get_retention_policy_stats(p_policy_id UUID)
RETURNS TABLE (
    total_executions BIGINT,
    successful_executions BIGINT,
    failed_executions BIGINT,
    total_records_deleted BIGINT,
    total_records_archived BIGINT,
    total_bytes_freed BIGINT,
    avg_execution_time_seconds NUMERIC,
    last_execution_at TIMESTAMP,
    last_execution_status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT AS total_executions,
        COUNT(CASE WHEN status = 'success' THEN 1 END)::BIGINT AS successful_executions,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)::BIGINT AS failed_executions,
        COALESCE(SUM(records_deleted), 0)::BIGINT AS total_records_deleted,
        COALESCE(SUM(records_archived), 0)::BIGINT AS total_records_archived,
        COALESCE(SUM(bytes_freed), 0)::BIGINT AS total_bytes_freed,
        COALESCE(AVG(duration_seconds), 0)::NUMERIC AS avg_execution_time_seconds,
        MAX(started_at) AS last_execution_at,
        (SELECT status FROM retention_executions
         WHERE policy_id = p_policy_id
         ORDER BY started_at DESC
         LIMIT 1) AS last_execution_status
    FROM retention_executions
    WHERE policy_id = p_policy_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_retention_policy_stats IS 'Get execution statistics for a retention policy';


-- =============================================================================
-- VIEW: Active Retention Policies
-- Purpose: View of enabled policies with next execution time
-- =============================================================================

CREATE OR REPLACE VIEW v_active_retention_policies AS
SELECT
    rp.*,
    CASE
        WHEN rp.last_executed_at IS NULL THEN NOW()
        ELSE rp.last_executed_at + INTERVAL '1 day'  -- Simplified: assumes daily
    END AS next_execution_estimate,
    (
        SELECT COUNT(*)
        FROM retention_executions re
        WHERE re.policy_id = rp.id
        AND re.status = 'success'
    ) AS successful_executions,
    (
        SELECT COUNT(*)
        FROM retention_executions re
        WHERE re.policy_id = rp.id
        AND re.status = 'failed'
    ) AS failed_executions
FROM retention_policies rp
WHERE rp.enabled = TRUE
ORDER BY rp.last_executed_at ASC NULLS FIRST;

COMMENT ON VIEW v_active_retention_policies IS 'Active retention policies with execution statistics';


-- =============================================================================
-- SAMPLE DATA: Default Retention Policies
-- Purpose: Create example retention policies for common use cases
-- =============================================================================

INSERT INTO retention_policies (name, description, data_type, retention_days, archive_before_delete, schedule)
VALUES
(
    'Telemetry Data - 90 Days',
    'Retain telemetry data for 90 days, then archive to cold storage',
    'telemetry',
    90,
    TRUE,
    '0 2 * * *'  -- Daily at 2 AM
),
(
    'Low-Severity Alerts - 30 Days',
    'Retain low and info severity alerts for 30 days, then delete',
    'alerts',
    30,
    FALSE,
    '0 3 * * 0'  -- Weekly on Sunday at 3 AM
),
(
    'Audit Logs - 1 Year',
    'Retain audit logs for 1 year for compliance, then archive',
    'audit_logs',
    365,
    TRUE,
    '0 4 1 * *'  -- Monthly on 1st at 4 AM
),
(
    'ML Anomalies - 180 Days',
    'Retain ML anomaly records for 180 days, then archive',
    'ml_anomalies',
    180,
    TRUE,
    '0 2 * * *'  -- Daily at 2 AM
)
ON CONFLICT (name) DO NOTHING;

-- Update filter criteria for low-severity alerts policy
UPDATE retention_policies
SET filter_criteria = '{"severity": ["low", "info"]}'::jsonb
WHERE name = 'Low-Severity Alerts - 30 Days';


-- =============================================================================
-- GRANT PERMISSIONS
-- Purpose: Allow iiot_user to access all retention tables and functions
-- =============================================================================

GRANT ALL PRIVILEGES ON TABLE retention_policies TO iiot_user;
GRANT ALL PRIVILEGES ON TABLE retention_executions TO iiot_user;
GRANT ALL PRIVILEGES ON TABLE archived_data_index TO iiot_user;

GRANT SELECT ON v_active_retention_policies TO iiot_user;

GRANT EXECUTE ON FUNCTION get_retention_policy_stats(UUID) TO iiot_user;
GRANT EXECUTE ON FUNCTION update_retention_policy_timestamp() TO iiot_user;
GRANT EXECUTE ON FUNCTION calculate_execution_duration() TO iiot_user;


-- =============================================================================
-- VERIFICATION QUERIES
-- Purpose: Verify schema deployment
-- =============================================================================

-- Check tables created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('retention_policies', 'retention_executions', 'archived_data_index')
ORDER BY table_name;

-- Check sample policies
SELECT name, data_type, retention_days, enabled
FROM retention_policies
ORDER BY retention_days;

-- Check view
SELECT COUNT(*) as active_policies
FROM v_active_retention_policies;


-- =============================================================================
-- DEPLOYMENT SUMMARY
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Data Retention Policies Schema Deployment Complete';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables Created: 3 (retention_policies, retention_executions, archived_data_index)';
    RAISE NOTICE 'Indexes Created: 12';
    RAISE NOTICE 'Triggers Created: 2 (timestamp update, duration calculation)';
    RAISE NOTICE 'Functions Created: 3 (stats, timestamp, duration)';
    RAISE NOTICE 'Views Created: 1 (active policies)';
    RAISE NOTICE 'Sample Policies: 4 (telemetry, alerts, audit logs, ML anomalies)';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Implement RetentionManager class in Python';
    RAISE NOTICE '2. Create retention API endpoints';
    RAISE NOTICE '3. Set up automated cleanup scheduler';
    RAISE NOTICE '4. Test retention policies';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Schema is ready for Data Retention implementation';
    RAISE NOTICE '=================================================================';
END $$;

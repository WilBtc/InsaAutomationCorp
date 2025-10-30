-- =====================================================================
-- Alert Grouping and Deduplication Schema
-- INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 8
-- Date: October 28, 2025
-- =====================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================
-- Table: alert_groups
-- Purpose: Group similar alerts to reduce noise
-- Grouping: device_id + rule_id + severity + time window
-- =====================================================================

CREATE TABLE IF NOT EXISTS alert_groups (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Grouping keys
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    rule_id UUID REFERENCES rules(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL,
    group_key TEXT NOT NULL,  -- Composite key: "device_id:rule_id:severity"

    -- Time tracking
    first_occurrence_at TIMESTAMPTZ NOT NULL,
    last_occurrence_at TIMESTAMPTZ NOT NULL,

    -- Statistics
    occurrence_count INTEGER NOT NULL DEFAULT 1,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active', 'closed'

    -- Representative alert (first alert in group)
    representative_alert_id UUID REFERENCES alerts(id) ON DELETE SET NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}',  -- Flexible storage for group-specific data

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    CHECK (status IN ('active', 'closed')),
    CHECK (occurrence_count > 0),
    CHECK (first_occurrence_at <= last_occurrence_at)
);

-- =====================================================================
-- Indexes for Performance
-- =====================================================================

-- Index on group_key for fast lookups
CREATE INDEX IF NOT EXISTS idx_alert_groups_group_key
ON alert_groups(group_key);

-- Index on status for querying active groups
CREATE INDEX IF NOT EXISTS idx_alert_groups_status
ON alert_groups(status);

-- Index on device_id for device-specific queries
CREATE INDEX IF NOT EXISTS idx_alert_groups_device
ON alert_groups(device_id);

-- Index on last_occurrence_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_alert_groups_last_occurrence
ON alert_groups(last_occurrence_at DESC);

-- Composite index for finding active groups by device
CREATE INDEX IF NOT EXISTS idx_alert_groups_device_status
ON alert_groups(device_id, status);

-- =====================================================================
-- Trigger: Update updated_at timestamp
-- =====================================================================

CREATE OR REPLACE FUNCTION update_alert_groups_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_alert_groups_timestamp
    BEFORE UPDATE ON alert_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_alert_groups_timestamp();

-- =====================================================================
-- View: Active alert groups
-- Purpose: Quick access to currently active groups
-- =====================================================================

CREATE OR REPLACE VIEW v_active_alert_groups AS
SELECT
    ag.*,
    d.name AS device_name,
    d.type AS device_type,
    r.name AS rule_name,
    a.message AS representative_message,
    -- Calculate noise reduction percentage
    CASE
        WHEN ag.occurrence_count > 1 THEN
            ((ag.occurrence_count - 1)::float / ag.occurrence_count * 100)::numeric(5,2)
        ELSE
            0
    END AS noise_reduction_pct,
    -- Calculate group age
    EXTRACT(EPOCH FROM (NOW() - ag.first_occurrence_at))/60 AS age_minutes
FROM
    alert_groups ag
    LEFT JOIN devices d ON ag.device_id = d.id
    LEFT JOIN rules r ON ag.rule_id = r.id
    LEFT JOIN alerts a ON ag.representative_alert_id = a.id
WHERE
    ag.status = 'active'
ORDER BY
    ag.last_occurrence_at DESC;

-- =====================================================================
-- View: Group statistics summary
-- Purpose: Aggregate statistics for monitoring
-- =====================================================================

CREATE OR REPLACE VIEW v_alert_group_stats AS
SELECT
    COUNT(*) AS total_groups,
    COUNT(*) FILTER (WHERE status = 'active') AS active_groups,
    COUNT(*) FILTER (WHERE status = 'closed') AS closed_groups,
    SUM(occurrence_count) AS total_alerts_grouped,
    AVG(occurrence_count) AS avg_alerts_per_group,
    MAX(occurrence_count) AS max_alerts_in_group,
    -- Overall noise reduction
    CASE
        WHEN SUM(occurrence_count) > COUNT(*) THEN
            ((SUM(occurrence_count) - COUNT(*))::float / SUM(occurrence_count) * 100)::numeric(5,2)
        ELSE
            0
    END AS overall_noise_reduction_pct
FROM
    alert_groups;

-- =====================================================================
-- Function: Find or create alert group
-- Purpose: Check if alert should join existing group or create new one
-- Returns: group_id (existing or new)
-- =====================================================================

CREATE OR REPLACE FUNCTION find_or_create_alert_group(
    p_device_id UUID,
    p_rule_id UUID,
    p_severity VARCHAR(20),
    p_alert_id UUID,
    p_time_window_minutes INTEGER DEFAULT 5
)
RETURNS UUID AS $$
DECLARE
    v_group_key TEXT;
    v_group_id UUID;
    v_cutoff_time TIMESTAMPTZ;
BEGIN
    -- Generate group key
    v_group_key := p_device_id::text || ':' || p_rule_id::text || ':' || p_severity;

    -- Calculate time window cutoff
    v_cutoff_time := NOW() - (p_time_window_minutes || ' minutes')::INTERVAL;

    -- Try to find existing active group within time window
    SELECT id INTO v_group_id
    FROM alert_groups
    WHERE
        group_key = v_group_key
        AND status = 'active'
        AND last_occurrence_at >= v_cutoff_time
    ORDER BY last_occurrence_at DESC
    LIMIT 1;

    -- If group found, update it
    IF v_group_id IS NOT NULL THEN
        UPDATE alert_groups
        SET
            occurrence_count = occurrence_count + 1,
            last_occurrence_at = NOW()
        WHERE id = v_group_id;

        -- Update alert to reference group
        UPDATE alerts
        SET grouped_alert_id = v_group_id
        WHERE id = p_alert_id;

        RETURN v_group_id;
    ELSE
        -- Create new group
        INSERT INTO alert_groups (
            device_id,
            rule_id,
            severity,
            group_key,
            first_occurrence_at,
            last_occurrence_at,
            occurrence_count,
            status,
            representative_alert_id
        )
        VALUES (
            p_device_id,
            p_rule_id,
            p_severity,
            v_group_key,
            NOW(),
            NOW(),
            1,
            'active',
            p_alert_id
        )
        RETURNING id INTO v_group_id;

        -- Update alert to reference group
        UPDATE alerts
        SET grouped_alert_id = v_group_id
        WHERE id = p_alert_id;

        RETURN v_group_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- Function: Close alert group
-- Purpose: Mark group as closed when condition resolved
-- =====================================================================

CREATE OR REPLACE FUNCTION close_alert_group(p_group_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE alert_groups
    SET status = 'closed'
    WHERE id = p_group_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- Function: Get group statistics
-- Purpose: Get detailed stats for a specific group
-- =====================================================================

CREATE OR REPLACE FUNCTION get_group_statistics(p_group_id UUID)
RETURNS TABLE (
    group_id UUID,
    device_name TEXT,
    rule_name TEXT,
    severity TEXT,
    occurrence_count INTEGER,
    first_occurrence TIMESTAMPTZ,
    last_occurrence TIMESTAMPTZ,
    age_minutes NUMERIC,
    noise_reduction_pct NUMERIC,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ag.id AS group_id,
        d.name AS device_name,
        r.name AS rule_name,
        ag.severity,
        ag.occurrence_count,
        ag.first_occurrence_at AS first_occurrence,
        ag.last_occurrence_at AS last_occurrence,
        EXTRACT(EPOCH FROM (NOW() - ag.first_occurrence_at))/60 AS age_minutes,
        CASE
            WHEN ag.occurrence_count > 1 THEN
                ((ag.occurrence_count - 1)::float / ag.occurrence_count * 100)::numeric(5,2)
            ELSE
                0
        END AS noise_reduction_pct,
        ag.status
    FROM
        alert_groups ag
        LEFT JOIN devices d ON ag.device_id = d.id
        LEFT JOIN rules r ON ag.rule_id = r.id
    WHERE
        ag.id = p_group_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- Grant Permissions
-- =====================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON alert_groups TO iiot_user;
GRANT SELECT ON v_active_alert_groups TO iiot_user;
GRANT SELECT ON v_alert_group_stats TO iiot_user;
GRANT EXECUTE ON FUNCTION find_or_create_alert_group(UUID, UUID, VARCHAR, UUID, INTEGER) TO iiot_user;
GRANT EXECUTE ON FUNCTION close_alert_group(UUID) TO iiot_user;
GRANT EXECUTE ON FUNCTION get_group_statistics(UUID) TO iiot_user;

-- =====================================================================
-- Verification Queries
-- =====================================================================

-- Check table exists
SELECT 'Table alert_groups created' AS status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'alert_groups'
);

-- Check indexes
SELECT 'Indexes created' AS status, COUNT(*) AS index_count
FROM pg_indexes
WHERE tablename = 'alert_groups';

-- Check views
SELECT 'Views created' AS status, COUNT(*) AS view_count
FROM information_schema.views
WHERE table_name IN ('v_active_alert_groups', 'v_alert_group_stats');

-- Check functions
SELECT 'Functions created' AS status, COUNT(*) AS function_count
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
AND p.proname IN (
    'find_or_create_alert_group',
    'close_alert_group',
    'get_group_statistics',
    'update_alert_groups_timestamp'
);

-- =====================================================================
-- END OF SCHEMA
-- =====================================================================

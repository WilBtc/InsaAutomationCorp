-- Migration: Convert esp_telemetry to TimescaleDB hypertable
-- Date: 2025-11-20
-- Description: Converts regular PostgreSQL tables to TimescaleDB hypertables for time-series optimization

-- ============================================================================
-- Step 1: Convert esp_telemetry to hypertable
-- ============================================================================

-- Check if already a hypertable
DO $$
BEGIN
    -- Try to convert to hypertable
    -- This will fail gracefully if already a hypertable
    BEGIN
        PERFORM create_hypertable(
            'esp_telemetry',
            'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE,
            migrate_data => TRUE  -- Migrate existing data
        );
        RAISE NOTICE 'esp_telemetry converted to hypertable';
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'esp_telemetry may already be a hypertable: %', SQLERRM;
    END;
END $$;

-- ============================================================================
-- Step 2: Add optimized indexes for time-series queries
-- ============================================================================

-- Index for well_id + timestamp (already exists, but recreate if needed)
CREATE INDEX IF NOT EXISTS idx_esp_telemetry_well_time
    ON esp_telemetry (well_id, timestamp DESC);

-- Index for timestamp only (for time-range queries)
CREATE INDEX IF NOT EXISTS idx_esp_telemetry_time
    ON esp_telemetry (timestamp DESC);

-- ============================================================================
-- Step 3: Convert diagnostic_results to hypertable (if exists)
-- ============================================================================

DO $$
BEGIN
    -- Check if diagnostic_results table exists
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'diagnostic_results') THEN
        -- Try to convert to hypertable
        BEGIN
            PERFORM create_hypertable(
                'diagnostic_results',
                'timestamp',
                chunk_time_interval => INTERVAL '7 days',  -- Weekly chunks for diagnostics
                if_not_exists => TRUE,
                migrate_data => TRUE
            );
            RAISE NOTICE 'diagnostic_results converted to hypertable';
        EXCEPTION
            WHEN others THEN
                RAISE NOTICE 'diagnostic_results may already be a hypertable: %', SQLERRM;
        END;

        -- Add indexes
        CREATE INDEX IF NOT EXISTS idx_diagnostic_well_time
            ON diagnostic_results (well_id, timestamp DESC);

        CREATE INDEX IF NOT EXISTS idx_diagnostic_severity
            ON diagnostic_results (severity, timestamp DESC);
    END IF;
END $$;

-- ============================================================================
-- Step 4: Set retention policies (30 days as per requirements)
-- ============================================================================

-- Add retention policy for esp_telemetry (30 days)
SELECT add_retention_policy('esp_telemetry', INTERVAL '30 days', if_not_exists => TRUE);

-- Add retention policy for diagnostic_results (90 days - keep diagnostics longer)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'diagnostic_results') THEN
        PERFORM add_retention_policy('diagnostic_results', INTERVAL '90 days', if_not_exists => TRUE);
    END IF;
END $$;

-- ============================================================================
-- Step 5: Verify hypertable creation
-- ============================================================================

-- Show all hypertables
SELECT
    hypertable_name,
    num_dimensions,
    num_chunks,
    compression_enabled,
    table_bytes,
    index_bytes,
    total_bytes
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'public';

-- Show chunk information
SELECT
    chunk_name,
    range_start,
    range_end
FROM timescaledb_information.chunks
WHERE hypertable_name = 'esp_telemetry'
ORDER BY range_start DESC
LIMIT 5;

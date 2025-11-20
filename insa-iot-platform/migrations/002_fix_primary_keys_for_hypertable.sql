-- Migration: Fix primary keys to allow TimescaleDB hypertable conversion
-- Date: 2025-11-20
-- Description: TimescaleDB requires the partitioning column (timestamp) to be part of the primary key

-- ============================================================================
-- Step 1: Fix esp_telemetry primary key
-- ============================================================================

-- Drop existing primary key constraint
ALTER TABLE esp_telemetry DROP CONSTRAINT IF EXISTS esp_telemetry_pkey CASCADE;

-- Add composite primary key (id + timestamp)
-- Note: We keep id as part of the key for backwards compatibility
ALTER TABLE esp_telemetry ADD PRIMARY KEY (id, timestamp);

-- ============================================================================
-- Step 2: Fix diagnostic_results primary key (if exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'diagnostic_results') THEN
        -- Drop existing primary key
        ALTER TABLE diagnostic_results DROP CONSTRAINT IF EXISTS diagnostic_results_pkey CASCADE;

        -- Add composite primary key
        ALTER TABLE diagnostic_results ADD PRIMARY KEY (id, timestamp);
    END IF;
END $$;

-- Verify the new primary keys
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE contype = 'p'
    AND connamespace = 'public'::regnamespace
    AND conrelid::regclass::text IN ('esp_telemetry', 'diagnostic_results');

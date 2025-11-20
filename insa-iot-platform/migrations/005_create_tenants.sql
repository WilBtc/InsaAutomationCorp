-- ============================================================================
-- Migration 005: Multi-Tenancy Implementation
-- ============================================================================
-- Purpose: Add complete multi-tenancy with customer isolation and resource quotas
-- Created: 2025-11-20
-- Week: 3
-- ============================================================================

-- ============================================================================
-- PART 1: Core Tenant Tables
-- ============================================================================

-- Create tenants table
-- ============================================================================
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,  -- URL-friendly identifier
    domain VARCHAR(255) UNIQUE,  -- Custom domain (optional)
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'inactive', 'trial')),
    plan VARCHAR(50) NOT NULL DEFAULT 'standard' CHECK (plan IN ('trial', 'standard', 'professional', 'enterprise')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMP,
    suspended_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    settings JSONB DEFAULT '{}'::jsonb,  -- Tenant-specific configuration
    CONSTRAINT tenants_name_check CHECK (length(name) >= 2),
    CONSTRAINT tenants_slug_check CHECK (slug ~ '^[a-z0-9-]+$')
);

-- Create indexes for tenants
CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);
CREATE INDEX IF NOT EXISTS idx_tenants_domain ON tenants(domain) WHERE domain IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_plan ON tenants(plan);
CREATE INDEX IF NOT EXISTS idx_tenants_created_at ON tenants(created_at DESC);

-- Add comments to tenants table
COMMENT ON TABLE tenants IS 'Multi-tenant customers with isolation and quotas';
COMMENT ON COLUMN tenants.id IS 'Unique tenant identifier';
COMMENT ON COLUMN tenants.name IS 'Tenant display name (e.g., "Alkhorayef Petroleum")';
COMMENT ON COLUMN tenants.slug IS 'URL-friendly identifier (e.g., "alkhorayef-petroleum")';
COMMENT ON COLUMN tenants.domain IS 'Custom domain for tenant (optional, e.g., "alkhorayef.example.com")';
COMMENT ON COLUMN tenants.status IS 'Tenant status: active, suspended, inactive, trial';
COMMENT ON COLUMN tenants.plan IS 'Subscription plan: trial, standard, professional, enterprise';
COMMENT ON COLUMN tenants.created_at IS 'Tenant creation timestamp';
COMMENT ON COLUMN tenants.updated_at IS 'Last update timestamp';
COMMENT ON COLUMN tenants.activated_at IS 'When tenant was activated';
COMMENT ON COLUMN tenants.suspended_at IS 'When tenant was suspended (if applicable)';
COMMENT ON COLUMN tenants.metadata IS 'Additional tenant metadata (contact info, billing, etc.)';
COMMENT ON COLUMN tenants.settings IS 'Tenant-specific configuration (features, preferences, etc.)';

-- ============================================================================
-- PART 2: Tenant Quotas and Resource Limits
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_quotas (
    tenant_id INTEGER PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    -- API quotas
    api_calls_per_hour INTEGER NOT NULL DEFAULT 10000,
    api_calls_per_day INTEGER NOT NULL DEFAULT 200000,
    api_burst_limit INTEGER NOT NULL DEFAULT 100,  -- Max concurrent requests

    -- Storage quotas
    storage_gb INTEGER NOT NULL DEFAULT 100,
    max_wells INTEGER NOT NULL DEFAULT 50,
    max_users INTEGER NOT NULL DEFAULT 10,

    -- Data retention
    retention_days INTEGER NOT NULL DEFAULT 30,
    backup_retention_days INTEGER NOT NULL DEFAULT 90,

    -- Feature flags
    features JSONB DEFAULT '{
        "advanced_analytics": true,
        "ml_predictions": false,
        "custom_alerts": true,
        "api_access": true,
        "export_data": true,
        "custom_reports": false
    }'::jsonb,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT quota_api_calls_hour_check CHECK (api_calls_per_hour > 0),
    CONSTRAINT quota_api_calls_day_check CHECK (api_calls_per_day > 0),
    CONSTRAINT quota_storage_check CHECK (storage_gb > 0),
    CONSTRAINT quota_wells_check CHECK (max_wells > 0),
    CONSTRAINT quota_users_check CHECK (max_users > 0),
    CONSTRAINT quota_retention_check CHECK (retention_days > 0)
);

-- Create indexes for tenant_quotas
CREATE INDEX IF NOT EXISTS idx_tenant_quotas_tenant_id ON tenant_quotas(tenant_id);

-- Add comments to tenant_quotas table
COMMENT ON TABLE tenant_quotas IS 'Resource quotas and limits per tenant';
COMMENT ON COLUMN tenant_quotas.tenant_id IS 'Reference to tenant';
COMMENT ON COLUMN tenant_quotas.api_calls_per_hour IS 'Maximum API calls per hour';
COMMENT ON COLUMN tenant_quotas.api_calls_per_day IS 'Maximum API calls per day';
COMMENT ON COLUMN tenant_quotas.api_burst_limit IS 'Maximum concurrent API requests';
COMMENT ON COLUMN tenant_quotas.storage_gb IS 'Maximum storage in gigabytes';
COMMENT ON COLUMN tenant_quotas.max_wells IS 'Maximum number of wells/assets';
COMMENT ON COLUMN tenant_quotas.max_users IS 'Maximum number of users';
COMMENT ON COLUMN tenant_quotas.retention_days IS 'Data retention period in days';
COMMENT ON COLUMN tenant_quotas.backup_retention_days IS 'Backup retention period in days';
COMMENT ON COLUMN tenant_quotas.features IS 'Feature flags (JSON)';

-- ============================================================================
-- PART 3: Tenant Usage Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_usage (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    metric VARCHAR(100) NOT NULL,  -- 'api_calls', 'storage_bytes', 'active_wells', etc.
    value BIGINT NOT NULL DEFAULT 0,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT usage_metric_check CHECK (metric IN ('api_calls', 'storage_bytes', 'active_wells', 'active_users', 'data_points'))
);

-- Create indexes for tenant_usage
CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_id ON tenant_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_usage_metric ON tenant_usage(metric);
CREATE INDEX IF NOT EXISTS idx_tenant_usage_period ON tenant_usage(period_start DESC, period_end DESC);
CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_period ON tenant_usage(tenant_id, period_start DESC);

-- Add comments
COMMENT ON TABLE tenant_usage IS 'Historical usage tracking per tenant';
COMMENT ON COLUMN tenant_usage.tenant_id IS 'Reference to tenant';
COMMENT ON COLUMN tenant_usage.metric IS 'Usage metric type';
COMMENT ON COLUMN tenant_usage.value IS 'Metric value';
COMMENT ON COLUMN tenant_usage.period_start IS 'Start of measurement period';
COMMENT ON COLUMN tenant_usage.period_end IS 'End of measurement period';

-- ============================================================================
-- PART 4: Add tenant_id to existing tables
-- ============================================================================

-- Add tenant_id to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id) WHERE tenant_id IS NOT NULL;

COMMENT ON COLUMN users.tenant_id IS 'Tenant the user belongs to (NULL for super-admins)';

-- Add super_admin flag to users
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_users_super_admin ON users(is_super_admin) WHERE is_super_admin = TRUE;

COMMENT ON COLUMN users.is_super_admin IS 'Cross-tenant super-admin access';

-- Add tenant_id to esp_telemetry table
ALTER TABLE esp_telemetry ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_esp_telemetry_tenant_id ON esp_telemetry(tenant_id, timestamp DESC) WHERE tenant_id IS NOT NULL;

COMMENT ON COLUMN esp_telemetry.tenant_id IS 'Tenant that owns this telemetry data';

-- ============================================================================
-- PART 5: Tenant-User Relationship (Many-to-Many)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'operator', 'viewer')),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,  -- Primary contact for tenant
    joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
    invited_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT tenant_users_unique UNIQUE (tenant_id, user_id)
);

-- Create indexes for tenant_users
CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant_id ON tenant_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_user_id ON tenant_users(user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_role ON tenant_users(tenant_id, role);
CREATE INDEX IF NOT EXISTS idx_tenant_users_primary ON tenant_users(tenant_id) WHERE is_primary = TRUE;

-- Add comments
COMMENT ON TABLE tenant_users IS 'Many-to-many relationship between tenants and users';
COMMENT ON COLUMN tenant_users.tenant_id IS 'Reference to tenant';
COMMENT ON COLUMN tenant_users.user_id IS 'Reference to user';
COMMENT ON COLUMN tenant_users.role IS 'User role within this tenant';
COMMENT ON COLUMN tenant_users.is_primary IS 'Whether this user is the primary contact';
COMMENT ON COLUMN tenant_users.joined_at IS 'When user joined the tenant';
COMMENT ON COLUMN tenant_users.invited_by IS 'User who invited this user';

-- ============================================================================
-- PART 6: Tenant-Wells Relationship
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_wells (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    well_id VARCHAR(255) NOT NULL,
    well_name VARCHAR(255),
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    added_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT tenant_wells_unique UNIQUE (tenant_id, well_id)
);

-- Create indexes for tenant_wells
CREATE INDEX IF NOT EXISTS idx_tenant_wells_tenant_id ON tenant_wells(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_wells_well_id ON tenant_wells(well_id);
CREATE INDEX IF NOT EXISTS idx_tenant_wells_status ON tenant_wells(tenant_id, status);

-- Add comments
COMMENT ON TABLE tenant_wells IS 'Wells/assets assigned to tenants';
COMMENT ON COLUMN tenant_wells.tenant_id IS 'Reference to tenant';
COMMENT ON COLUMN tenant_wells.well_id IS 'Unique well identifier';
COMMENT ON COLUMN tenant_wells.well_name IS 'Human-readable well name';
COMMENT ON COLUMN tenant_wells.location IS 'Well location';
COMMENT ON COLUMN tenant_wells.status IS 'Well status: active, inactive, maintenance';
COMMENT ON COLUMN tenant_wells.added_at IS 'When well was added to tenant';

-- ============================================================================
-- PART 7: Row-Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on esp_telemetry
ALTER TABLE esp_telemetry ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for tenant isolation
-- Note: This uses application-level tenant_id setting, not database roles
DROP POLICY IF EXISTS tenant_isolation_policy ON esp_telemetry;
CREATE POLICY tenant_isolation_policy ON esp_telemetry
    USING (
        tenant_id IS NULL  -- Allow data without tenant_id (legacy)
        OR tenant_id::text = current_setting('app.current_tenant_id', true)  -- Match current tenant
        OR current_setting('app.is_super_admin', true) = 'true'  -- Super-admins can see all
    );

-- Create policy for INSERT operations
DROP POLICY IF EXISTS tenant_insert_policy ON esp_telemetry;
CREATE POLICY tenant_insert_policy ON esp_telemetry
    FOR INSERT
    WITH CHECK (
        tenant_id::text = current_setting('app.current_tenant_id', true)
        OR current_setting('app.is_super_admin', true) = 'true'
    );

-- Add comments
COMMENT ON POLICY tenant_isolation_policy ON esp_telemetry IS 'Row-level security for tenant data isolation';
COMMENT ON POLICY tenant_insert_policy ON esp_telemetry IS 'Ensure data is inserted with correct tenant_id';

-- ============================================================================
-- PART 8: Tenant Management Functions
-- ============================================================================

-- Function to create a new tenant with default quotas
-- ============================================================================
CREATE OR REPLACE FUNCTION create_tenant(
    p_name VARCHAR(255),
    p_slug VARCHAR(255),
    p_domain VARCHAR(255) DEFAULT NULL,
    p_plan VARCHAR(50) DEFAULT 'standard',
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS INTEGER AS $$
DECLARE
    v_tenant_id INTEGER;
    v_quota_multiplier NUMERIC;
BEGIN
    -- Insert tenant
    INSERT INTO tenants (name, slug, domain, status, plan, created_at, activated_at, metadata)
    VALUES (p_name, p_slug, p_domain, 'active', p_plan, NOW(), NOW(), p_metadata)
    RETURNING id INTO v_tenant_id;

    -- Determine quota multiplier based on plan
    v_quota_multiplier := CASE p_plan
        WHEN 'trial' THEN 0.2
        WHEN 'standard' THEN 1.0
        WHEN 'professional' THEN 3.0
        WHEN 'enterprise' THEN 10.0
        ELSE 1.0
    END;

    -- Insert default quotas based on plan
    INSERT INTO tenant_quotas (
        tenant_id,
        api_calls_per_hour,
        api_calls_per_day,
        api_burst_limit,
        storage_gb,
        max_wells,
        max_users,
        retention_days,
        backup_retention_days,
        features
    ) VALUES (
        v_tenant_id,
        (10000 * v_quota_multiplier)::INTEGER,
        (200000 * v_quota_multiplier)::INTEGER,
        (100 * v_quota_multiplier)::INTEGER,
        (100 * v_quota_multiplier)::INTEGER,
        (50 * v_quota_multiplier)::INTEGER,
        (10 * v_quota_multiplier)::INTEGER,
        30,
        90,
        CASE p_plan
            WHEN 'trial' THEN '{"advanced_analytics": false, "ml_predictions": false, "custom_alerts": true, "api_access": true, "export_data": false, "custom_reports": false}'::jsonb
            WHEN 'enterprise' THEN '{"advanced_analytics": true, "ml_predictions": true, "custom_alerts": true, "api_access": true, "export_data": true, "custom_reports": true}'::jsonb
            ELSE '{"advanced_analytics": true, "ml_predictions": false, "custom_alerts": true, "api_access": true, "export_data": true, "custom_reports": false}'::jsonb
        END
    );

    RETURN v_tenant_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_tenant IS 'Create a new tenant with default quotas based on plan';

-- Function to check if tenant is within quota
-- ============================================================================
CREATE OR REPLACE FUNCTION check_tenant_quota(
    p_tenant_id INTEGER,
    p_metric VARCHAR(100),
    p_current_value BIGINT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_limit BIGINT;
BEGIN
    -- Get the appropriate quota limit
    SELECT
        CASE p_metric
            WHEN 'api_calls_hour' THEN api_calls_per_hour
            WHEN 'api_calls_day' THEN api_calls_per_day
            WHEN 'storage_gb' THEN storage_gb
            WHEN 'wells' THEN max_wells
            WHEN 'users' THEN max_users
            ELSE NULL
        END
    INTO v_limit
    FROM tenant_quotas
    WHERE tenant_id = p_tenant_id;

    -- If no limit found, deny
    IF v_limit IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check if current value is within limit
    RETURN p_current_value < v_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_tenant_quota IS 'Check if tenant is within quota limits';

-- Function to get tenant usage summary
-- ============================================================================
CREATE OR REPLACE FUNCTION get_tenant_usage(
    p_tenant_id INTEGER,
    p_period_hours INTEGER DEFAULT 24
)
RETURNS TABLE (
    metric VARCHAR(100),
    current_value BIGINT,
    quota_limit BIGINT,
    usage_percent NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH current_usage AS (
        SELECT 'api_calls' AS metric, COUNT(*)::BIGINT AS value
        FROM auth_audit_log
        WHERE user_id IN (SELECT user_id FROM tenant_users WHERE tenant_id = p_tenant_id)
          AND timestamp > NOW() - (p_period_hours || ' hours')::INTERVAL

        UNION ALL

        SELECT 'storage_gb' AS metric,
               (pg_total_relation_size('esp_telemetry')::BIGINT / (1024*1024*1024))::BIGINT AS value
        WHERE EXISTS (SELECT 1 FROM tenants WHERE id = p_tenant_id)

        UNION ALL

        SELECT 'active_wells' AS metric, COUNT(*)::BIGINT AS value
        FROM tenant_wells
        WHERE tenant_id = p_tenant_id AND status = 'active'

        UNION ALL

        SELECT 'active_users' AS metric, COUNT(*)::BIGINT AS value
        FROM tenant_users
        WHERE tenant_id = p_tenant_id
    )
    SELECT
        u.metric,
        u.value AS current_value,
        CASE u.metric
            WHEN 'api_calls' THEN q.api_calls_per_hour
            WHEN 'storage_gb' THEN q.storage_gb
            WHEN 'active_wells' THEN q.max_wells
            WHEN 'active_users' THEN q.max_users
            ELSE 0
        END AS quota_limit,
        CASE
            WHEN CASE u.metric
                WHEN 'api_calls' THEN q.api_calls_per_hour
                WHEN 'storage_gb' THEN q.storage_gb
                WHEN 'active_wells' THEN q.max_wells
                WHEN 'active_users' THEN q.max_users
                ELSE 1
            END > 0
            THEN ROUND((u.value::NUMERIC / CASE u.metric
                WHEN 'api_calls' THEN q.api_calls_per_hour
                WHEN 'storage_gb' THEN q.storage_gb
                WHEN 'active_wells' THEN q.max_wells
                WHEN 'active_users' THEN q.max_users
                ELSE 1
            END) * 100, 2)
            ELSE 0
        END AS usage_percent
    FROM current_usage u
    CROSS JOIN tenant_quotas q
    WHERE q.tenant_id = p_tenant_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_tenant_usage IS 'Get current usage statistics for a tenant';

-- Function to update tenant updated_at timestamp
-- ============================================================================
CREATE OR REPLACE FUNCTION update_tenant_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic timestamp updates
DROP TRIGGER IF EXISTS tenant_update_timestamp ON tenants;
CREATE TRIGGER tenant_update_timestamp
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_tenant_timestamp();

DROP TRIGGER IF EXISTS tenant_quota_update_timestamp ON tenant_quotas;
CREATE TRIGGER tenant_quota_update_timestamp
    BEFORE UPDATE ON tenant_quotas
    FOR EACH ROW
    EXECUTE FUNCTION update_tenant_timestamp();

-- ============================================================================
-- PART 9: Audit Logging for Multi-Tenancy
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_audit_log (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),  -- 'user', 'well', 'quota', 'settings'
    resource_id VARCHAR(255),
    changes JSONB,  -- Before/after values
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for tenant_audit_log
CREATE INDEX IF NOT EXISTS idx_tenant_audit_tenant_id ON tenant_audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_audit_user_id ON tenant_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_audit_action ON tenant_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_tenant_audit_timestamp ON tenant_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tenant_audit_resource ON tenant_audit_log(resource_type, resource_id);

-- Add comments
COMMENT ON TABLE tenant_audit_log IS 'Audit trail for tenant-related operations';
COMMENT ON COLUMN tenant_audit_log.tenant_id IS 'Tenant this action relates to';
COMMENT ON COLUMN tenant_audit_log.user_id IS 'User who performed the action';
COMMENT ON COLUMN tenant_audit_log.action IS 'Action performed (create, update, delete, etc.)';
COMMENT ON COLUMN tenant_audit_log.resource_type IS 'Type of resource affected';
COMMENT ON COLUMN tenant_audit_log.resource_id IS 'ID of affected resource';
COMMENT ON COLUMN tenant_audit_log.changes IS 'JSON object with before/after values';

-- Function to log tenant events
-- ============================================================================
CREATE OR REPLACE FUNCTION log_tenant_event(
    p_tenant_id INTEGER,
    p_user_id INTEGER,
    p_action VARCHAR(100),
    p_resource_type VARCHAR(100) DEFAULT NULL,
    p_resource_id VARCHAR(255) DEFAULT NULL,
    p_changes JSONB DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO tenant_audit_log (
        tenant_id,
        user_id,
        action,
        resource_type,
        resource_id,
        changes,
        metadata,
        timestamp
    ) VALUES (
        p_tenant_id,
        p_user_id,
        p_action,
        p_resource_type,
        p_resource_id,
        p_changes,
        p_metadata,
        NOW()
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_tenant_event IS 'Log a tenant-related event for audit trail';

-- ============================================================================
-- PART 10: Default Data and Verification
-- ============================================================================

-- Create default "System" tenant for legacy data
INSERT INTO tenants (id, name, slug, domain, status, plan, created_at, activated_at)
VALUES (1, 'System', 'system', NULL, 'active', 'enterprise', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Create default quotas for system tenant (unlimited)
INSERT INTO tenant_quotas (
    tenant_id,
    api_calls_per_hour,
    api_calls_per_day,
    api_burst_limit,
    storage_gb,
    max_wells,
    max_users,
    retention_days,
    backup_retention_days,
    features
) VALUES (
    1,
    1000000,
    10000000,
    1000,
    10000,
    1000,
    100,
    365,
    730,
    '{"advanced_analytics": true, "ml_predictions": true, "custom_alerts": true, "api_access": true, "export_data": true, "custom_reports": true}'::jsonb
)
ON CONFLICT (tenant_id) DO NOTHING;

-- Update sequence to start after system tenant
SELECT setval('tenants_id_seq', (SELECT MAX(id) FROM tenants), true);

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check all tenant-related tables
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('tenants', 'tenant_quotas', 'tenant_usage', 'tenant_users', 'tenant_wells', 'tenant_audit_log')
ORDER BY table_name;

-- Check indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('tenants', 'tenant_quotas', 'tenant_usage', 'tenant_users', 'tenant_wells', 'tenant_audit_log')
ORDER BY tablename, indexname;

-- Check RLS policies
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'esp_telemetry'
ORDER BY tablename, policyname;

-- ============================================================================
-- End of Migration 005
-- ============================================================================

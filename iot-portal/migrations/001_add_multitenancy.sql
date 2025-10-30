-- ============================================================================
-- Multi-tenancy Database Migration
-- INSA Advanced IIoT Platform v2.0 - Phase 3 Feature 6 (Phase 1)
--
-- This migration adds multi-tenancy support to the INSA IIoT platform.
--
-- Changes:
-- 1. Creates 3 new tables: tenants, tenant_users, tenant_invitations
-- 2. Adds tenant_id column to all existing tables
-- 3. Creates indexes on tenant_id for performance
-- 4. Creates default tenant for existing data
-- 5. Migrates all existing data to default tenant
--
-- Author: INSA Automation Corp
-- Date: October 28, 2025
--
-- IMPORTANT: Run this migration during maintenance window
-- Estimated execution time: 30-60 seconds
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Create new tables
-- ============================================================================

-- Tenants table: Master table of all organizations
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic info
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    domain VARCHAR(255),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'trial', 'churned')),
    tier VARCHAR(50) NOT NULL DEFAULT 'starter' CHECK (tier IN ('starter', 'professional', 'enterprise')),

    -- Branding
    logo_url TEXT,
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),

    -- Quotas (NULL = unlimited)
    max_devices INTEGER CHECK (max_devices IS NULL OR max_devices > 0),
    max_users INTEGER CHECK (max_users IS NULL OR max_users > 0),
    max_telemetry_points_per_day INTEGER CHECK (max_telemetry_points_per_day IS NULL OR max_telemetry_points_per_day > 0),
    max_retention_days INTEGER DEFAULT 90 CHECK (max_retention_days IS NULL OR max_retention_days > 0),

    -- Features (JSON for flexibility)
    enabled_features JSONB DEFAULT '{"ml": true, "advanced_analytics": true, "mobile": true, "retention": true}'::jsonb,

    -- Billing
    billing_email VARCHAR(255),
    billing_plan VARCHAR(50) CHECK (billing_plan IS NULL OR billing_plan IN ('monthly', 'annual')),
    billing_cycle_start DATE,
    billing_cycle_end DATE,
    mrr DECIMAL(10, 2) CHECK (mrr IS NULL OR mrr >= 0),

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID,
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE tenants IS 'Multi-tenant organizations using the INSA IIoT platform';
COMMENT ON COLUMN tenants.slug IS 'URL-friendly identifier for tenant (e.g., acme-corp)';
COMMENT ON COLUMN tenants.enabled_features IS 'JSON object of enabled features per tenant';
COMMENT ON COLUMN tenants.mrr IS 'Monthly Recurring Revenue in USD';

-- Tenant users table: Maps users to tenants with roles
CREATE TABLE IF NOT EXISTS tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id),

    -- Permissions
    is_tenant_admin BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, user_id)
);

COMMENT ON TABLE tenant_users IS 'Maps users to tenants with role assignments';
COMMENT ON COLUMN tenant_users.is_tenant_admin IS 'Can manage tenant settings and invite users';

-- Tenant invitations table: Manage pending user invitations
CREATE TABLE IF NOT EXISTS tenant_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id),

    -- Invitation
    token VARCHAR(255) NOT NULL UNIQUE,
    invited_by UUID NOT NULL REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    accepted_by UUID REFERENCES users(id),

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CHECK (expires_at > created_at)
);

COMMENT ON TABLE tenant_invitations IS 'Pending user invitations to tenants';
COMMENT ON COLUMN tenant_invitations.token IS 'Secure invitation token (UUID v4)';

-- ============================================================================
-- Step 2: Create indexes on new tables
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_created_at ON tenants(created_at);

CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_user ON tenant_users(user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_role ON tenant_users(role_id);

CREATE INDEX IF NOT EXISTS idx_invitations_tenant ON tenant_invitations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON tenant_invitations(email);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON tenant_invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_expires ON tenant_invitations(expires_at);

-- ============================================================================
-- Step 3: Add tenant_id columns to existing tables
-- ============================================================================

-- Core tables
ALTER TABLE devices ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE rules ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Phase 3 tables
ALTER TABLE ml_models ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE anomaly_detections ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE retention_policies ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE retention_executions ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE archived_data_index ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Advanced alerting tables (only tables that exist)
ALTER TABLE alert_states ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE alert_slas ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE escalation_policies ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE on_call_schedules ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE alert_groups ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- ============================================================================
-- Step 4: Create default tenant and migrate existing data
-- ============================================================================

DO $$
DECLARE
    default_tenant_id UUID;
    admin_user_id UUID;
    admin_role_id INTEGER;
BEGIN
    -- Create default tenant for existing data
    INSERT INTO tenants (
        name,
        slug,
        status,
        tier,
        max_devices,
        max_users,
        max_retention_days,
        enabled_features,
        metadata
    )
    VALUES (
        'INSA Automation Corp',
        'insa-default',
        'active',
        'enterprise',
        NULL,  -- Unlimited devices
        NULL,  -- Unlimited users
        NULL,  -- Unlimited retention
        '{"ml": true, "advanced_analytics": true, "advanced_alerting": true, "mobile": true, "retention": true, "rbac": true}'::jsonb,
        '{"is_default": true, "migrated_at": "2025-10-28T23:40:00Z"}'::jsonb
    )
    ON CONFLICT (slug) DO NOTHING
    RETURNING id INTO default_tenant_id;

    -- If tenant already exists, get its ID
    IF default_tenant_id IS NULL THEN
        SELECT id INTO default_tenant_id FROM tenants WHERE slug = 'insa-default';
    END IF;

    RAISE NOTICE 'Default tenant created: % (ID: %)', 'INSA Automation Corp', default_tenant_id;

    -- Migrate existing data to default tenant

    -- Core tables
    UPDATE devices SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE telemetry SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE rules SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE alerts SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE api_keys SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;

    -- Phase 3 tables
    UPDATE ml_models SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE anomaly_detections SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE retention_policies SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE retention_executions SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE archived_data_index SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;

    -- Advanced alerting tables (only tables that exist)
    UPDATE alert_states SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE alert_slas SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE escalation_policies SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE on_call_schedules SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;
    UPDATE alert_groups SET tenant_id = default_tenant_id WHERE tenant_id IS NULL;

    RAISE NOTICE 'Existing data migrated to default tenant';

    -- Map all existing users to default tenant with admin role
    SELECT id INTO admin_role_id FROM roles WHERE name = 'admin' LIMIT 1;

    -- Add all users to default tenant as admins
    INSERT INTO tenant_users (tenant_id, user_id, role_id, is_tenant_admin)
    SELECT default_tenant_id, u.id, admin_role_id, TRUE
    FROM users u
    WHERE NOT EXISTS (
        SELECT 1 FROM tenant_users tu
        WHERE tu.tenant_id = default_tenant_id AND tu.user_id = u.id
    );

    RAISE NOTICE 'Existing users added to default tenant';

END $$;

-- ============================================================================
-- Step 5: Make tenant_id NOT NULL after migration
-- ============================================================================

-- Core tables
ALTER TABLE devices ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE telemetry ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE rules ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE alerts ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE api_keys ALTER COLUMN tenant_id SET NOT NULL;

-- Phase 3 tables
ALTER TABLE ml_models ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE anomaly_detections ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE retention_policies ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE retention_executions ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE archived_data_index ALTER COLUMN tenant_id SET NOT NULL;

-- Advanced alerting tables (only tables that exist)
ALTER TABLE alert_states ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE alert_slas ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE escalation_policies ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE on_call_schedules ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE alert_groups ALTER COLUMN tenant_id SET NOT NULL;

-- ============================================================================
-- Step 6: Create indexes on tenant_id columns for performance
-- ============================================================================

-- Core tables
CREATE INDEX IF NOT EXISTS idx_devices_tenant ON devices(tenant_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_tenant ON telemetry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_tenant_device ON telemetry(tenant_id, device_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_tenant_timestamp ON telemetry(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_rules_tenant ON rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alerts_tenant ON alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alerts_tenant_severity ON alerts(tenant_id, severity);
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON api_keys(tenant_id);

-- Phase 3 tables
CREATE INDEX IF NOT EXISTS idx_ml_models_tenant ON ml_models(tenant_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_detections_tenant ON anomaly_detections(tenant_id);
CREATE INDEX IF NOT EXISTS idx_retention_policies_tenant ON retention_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_retention_executions_tenant ON retention_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_archived_data_index_tenant ON archived_data_index(tenant_id);

-- Advanced alerting tables (only tables that exist)
CREATE INDEX IF NOT EXISTS idx_alert_states_tenant ON alert_states(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alert_slas_tenant ON alert_slas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_escalation_policies_tenant ON escalation_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_on_call_schedules_tenant ON on_call_schedules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alert_groups_tenant ON alert_groups(tenant_id);

-- ============================================================================
-- Step 7: Create helper functions for tenant management
-- ============================================================================

-- Function to get tenant statistics
CREATE OR REPLACE FUNCTION get_tenant_stats(p_tenant_id UUID)
RETURNS TABLE (
    tenant_id UUID,
    tenant_name VARCHAR,
    device_count BIGINT,
    user_count BIGINT,
    rule_count BIGINT,
    alert_count_24h BIGINT,
    telemetry_points_24h BIGINT,
    quota_devices_used INTEGER,
    quota_devices_max INTEGER,
    quota_devices_percent NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.name,
        (SELECT COUNT(*) FROM devices WHERE tenant_id = p_tenant_id),
        (SELECT COUNT(*) FROM tenant_users WHERE tenant_id = p_tenant_id),
        (SELECT COUNT(*) FROM rules WHERE tenant_id = p_tenant_id AND enabled = TRUE),
        (SELECT COUNT(*) FROM alerts WHERE tenant_id = p_tenant_id AND created_at > NOW() - INTERVAL '24 hours'),
        (SELECT COUNT(*) FROM telemetry WHERE tenant_id = p_tenant_id AND timestamp > NOW() - INTERVAL '24 hours'),
        (SELECT COUNT(*)::INTEGER FROM devices WHERE tenant_id = p_tenant_id),
        t.max_devices,
        CASE
            WHEN t.max_devices IS NULL THEN 0
            ELSE (SELECT COUNT(*)::NUMERIC / t.max_devices::NUMERIC * 100 FROM devices WHERE tenant_id = p_tenant_id)
        END
    FROM tenants t
    WHERE t.id = p_tenant_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_tenant_stats IS 'Get comprehensive statistics for a tenant';

-- Function to check if tenant can add device (quota check)
CREATE OR REPLACE FUNCTION check_tenant_device_quota(p_tenant_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    current_count INTEGER;
    max_quota INTEGER;
BEGIN
    SELECT max_devices INTO max_quota FROM tenants WHERE id = p_tenant_id;

    -- NULL means unlimited
    IF max_quota IS NULL THEN
        RETURN TRUE;
    END IF;

    SELECT COUNT(*)::INTEGER INTO current_count FROM devices WHERE tenant_id = p_tenant_id;

    RETURN current_count < max_quota;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_tenant_device_quota IS 'Check if tenant can add more devices';

-- Function to check if tenant can add user (quota check)
CREATE OR REPLACE FUNCTION check_tenant_user_quota(p_tenant_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    current_count INTEGER;
    max_quota INTEGER;
BEGIN
    SELECT max_users INTO max_quota FROM tenants WHERE id = p_tenant_id;

    -- NULL means unlimited
    IF max_quota IS NULL THEN
        RETURN TRUE;
    END IF;

    SELECT COUNT(*)::INTEGER INTO current_count FROM tenant_users WHERE tenant_id = p_tenant_id;

    RETURN current_count < max_quota;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_tenant_user_quota IS 'Check if tenant can add more users';

-- ============================================================================
-- Step 8: Create trigger to update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_tenant_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tenant_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_tenant_updated_at();

CREATE TRIGGER trigger_tenant_users_updated_at
    BEFORE UPDATE ON tenant_users
    FOR EACH ROW
    EXECUTE FUNCTION update_tenant_updated_at();

-- ============================================================================
-- Step 9: Create view for tenant dashboard
-- ============================================================================

CREATE OR REPLACE VIEW tenant_dashboard AS
SELECT
    t.id,
    t.name,
    t.slug,
    t.status,
    t.tier,
    t.created_at,
    COUNT(DISTINCT d.id) as device_count,
    COUNT(DISTINCT tu.user_id) as user_count,
    COUNT(DISTINCT r.id) as rule_count,
    COUNT(DISTINCT a.id) FILTER (WHERE a.created_at > NOW() - INTERVAL '24 hours') as alerts_24h,
    t.max_devices,
    t.max_users,
    t.enabled_features,
    CASE
        WHEN t.max_devices IS NOT NULL THEN
            ROUND((COUNT(DISTINCT d.id)::NUMERIC / t.max_devices::NUMERIC * 100), 2)
        ELSE NULL
    END as device_quota_percent,
    CASE
        WHEN t.max_users IS NOT NULL THEN
            ROUND((COUNT(DISTINCT tu.user_id)::NUMERIC / t.max_users::NUMERIC * 100), 2)
        ELSE NULL
    END as user_quota_percent
FROM tenants t
LEFT JOIN devices d ON d.tenant_id = t.id
LEFT JOIN tenant_users tu ON tu.tenant_id = t.id
LEFT JOIN rules r ON r.tenant_id = t.id AND r.enabled = TRUE
LEFT JOIN alerts a ON a.tenant_id = t.id
GROUP BY t.id, t.name, t.slug, t.status, t.tier, t.created_at, t.max_devices, t.max_users, t.enabled_features;

COMMENT ON VIEW tenant_dashboard IS 'Comprehensive tenant dashboard with usage stats';

-- ============================================================================
-- Step 10: Grant permissions (if using separate application user)
-- ============================================================================

-- Grant permissions to iiot_user (application user)
GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO iiot_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_users TO iiot_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_invitations TO iiot_user;
GRANT SELECT ON tenant_dashboard TO iiot_user;
GRANT EXECUTE ON FUNCTION get_tenant_stats TO iiot_user;
GRANT EXECUTE ON FUNCTION check_tenant_device_quota TO iiot_user;
GRANT EXECUTE ON FUNCTION check_tenant_user_quota TO iiot_user;

-- ============================================================================
-- Migration complete!
-- ============================================================================

COMMIT;

-- Verify migration
DO $$
DECLARE
    tenant_count INTEGER;
    default_tenant_id UUID;
    device_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO tenant_count FROM tenants;
    SELECT id INTO default_tenant_id FROM tenants WHERE slug = 'insa-default';
    SELECT COUNT(*) INTO device_count FROM devices WHERE tenant_id = default_tenant_id;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tenants created: %', tenant_count;
    RAISE NOTICE 'Default tenant ID: %', default_tenant_id;
    RAISE NOTICE 'Devices migrated: %', device_count;
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Implement TenantContextMiddleware in app_advanced.py';
    RAISE NOTICE '2. Update JWT token generation to include tenant_id';
    RAISE NOTICE '3. Add @require_tenant decorator to all endpoints';
    RAISE NOTICE '4. Test tenant isolation';
    RAISE NOTICE '========================================';
END $$;

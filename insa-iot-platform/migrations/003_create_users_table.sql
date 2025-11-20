-- ============================================================================
-- Migration 003: Create Users and Authentication Tables
-- ============================================================================
-- Purpose: Add JWT authentication with role-based access control (RBAC)
-- Created: 2025-11-20
-- ============================================================================

-- Create users table
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- Add comments to users table
COMMENT ON TABLE users IS 'User accounts for authentication and authorization';
COMMENT ON COLUMN users.id IS 'Unique user identifier';
COMMENT ON COLUMN users.username IS 'Unique username for login';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password';
COMMENT ON COLUMN users.role IS 'User role for RBAC: admin, operator, viewer';
COMMENT ON COLUMN users.created_at IS 'Account creation timestamp';
COMMENT ON COLUMN users.last_login IS 'Last successful login timestamp';
COMMENT ON COLUMN users.is_active IS 'Whether the account is active';
COMMENT ON COLUMN users.metadata IS 'Additional user metadata (JSON)';

-- Create refresh_tokens table
-- ============================================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_used TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for refresh_tokens table
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- Add comments to refresh_tokens table
COMMENT ON TABLE refresh_tokens IS 'Refresh tokens for JWT token renewal';
COMMENT ON COLUMN refresh_tokens.id IS 'Unique token identifier';
COMMENT ON COLUMN refresh_tokens.token IS 'JWT refresh token string';
COMMENT ON COLUMN refresh_tokens.user_id IS 'Associated user ID';
COMMENT ON COLUMN refresh_tokens.created_at IS 'Token creation timestamp';
COMMENT ON COLUMN refresh_tokens.expires_at IS 'Token expiration timestamp';
COMMENT ON COLUMN refresh_tokens.last_used IS 'Last time token was used';
COMMENT ON COLUMN refresh_tokens.metadata IS 'Additional token metadata (JSON)';

-- Create audit log table for security tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS auth_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for auth_audit_log table
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_user_id ON auth_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_username ON auth_audit_log(username);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_action ON auth_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_timestamp ON auth_audit_log(timestamp DESC);

-- Add comments to auth_audit_log table
COMMENT ON TABLE auth_audit_log IS 'Audit log for authentication and authorization events';
COMMENT ON COLUMN auth_audit_log.id IS 'Unique log entry identifier';
COMMENT ON COLUMN auth_audit_log.user_id IS 'User ID (null if user deleted)';
COMMENT ON COLUMN auth_audit_log.username IS 'Username at time of event';
COMMENT ON COLUMN auth_audit_log.action IS 'Action type (login, logout, token_refresh, etc.)';
COMMENT ON COLUMN auth_audit_log.status IS 'Action status (success, failure, error)';
COMMENT ON COLUMN auth_audit_log.ip_address IS 'Client IP address';
COMMENT ON COLUMN auth_audit_log.user_agent IS 'Client user agent string';
COMMENT ON COLUMN auth_audit_log.timestamp IS 'Event timestamp';
COMMENT ON COLUMN auth_audit_log.metadata IS 'Additional event metadata (JSON)';

-- Create function to automatically clean expired tokens
-- ============================================================================
CREATE OR REPLACE FUNCTION clean_expired_refresh_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM refresh_tokens
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION clean_expired_refresh_tokens() IS 'Delete expired refresh tokens and return count';

-- Create function to log authentication events
-- ============================================================================
CREATE OR REPLACE FUNCTION log_auth_event(
    p_user_id INTEGER,
    p_username VARCHAR(255),
    p_action VARCHAR(100),
    p_status VARCHAR(50),
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO auth_audit_log (
        user_id,
        username,
        action,
        status,
        ip_address,
        user_agent,
        timestamp,
        metadata
    ) VALUES (
        p_user_id,
        p_username,
        p_action,
        p_status,
        p_ip_address,
        p_user_agent,
        NOW(),
        p_metadata
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_auth_event IS 'Log an authentication/authorization event';

-- Grant permissions (adjust as needed for your environment)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON users TO your_app_user;
-- GRANT SELECT, INSERT, DELETE ON refresh_tokens TO your_app_user;
-- GRANT INSERT ON auth_audit_log TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Verification queries
-- ============================================================================
-- Uncomment to verify the migration

-- SELECT table_name, column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name IN ('users', 'refresh_tokens', 'auth_audit_log')
-- ORDER BY table_name, ordinal_position;

-- SELECT indexname, tablename, indexdef
-- FROM pg_indexes
-- WHERE tablename IN ('users', 'refresh_tokens', 'auth_audit_log')
-- ORDER BY tablename, indexname;

-- ============================================================================
-- End of Migration 003
-- ============================================================================
